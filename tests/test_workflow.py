"""Workflow tests for FlowDesk.

Tests cover each LangGraph node (intake, classification, routing, SLA)
independently as well as the full end-to-end workflow.
"""

import pytest

# Import from backend.workflow and backend.models


from pathlib import Path
from backend import db, constants, models, workflow
from backend.models import GraphState

# Override DB path for isolation
constants.DB_PATH = "data/test_flowdesk.db"


def setup_module(module):
    # Ensure fresh DB and user seeded
    db_path = Path(constants.DB_PATH)
    if db_path.exists():
        try:
            db_path.unlink()
        except Exception:
            pass
    db.init_db()

    # Seed a user to look up by telegram_id
    student_user = models.UserCreate(
        name="Alice Smith",
        role="student",
        telegram_id="987654321",
        department=None
    )
    db.create_user(student_user)


def teardown_module(module):
    db_path = Path(constants.DB_PATH)
    if db_path.exists():
        try:
            db_path.unlink()
        except Exception:
            pass


def test_intake_node() -> None:
    """Test intake agent processes raw message."""
    initial_state: GraphState = {
        "raw_message": "Wi-Fi not working in Hostel Block A",
        "telegram_id": "987654321",
        "student_id": None,
        "ticket_id": None,
        "title": None,
        "description": "",
        "category": None,
        "location": "Unknown",
        "priority": None,
        "assigned_dept": None,
        "sla_deadline": None,
        "status": "Open",
        "created_at": None,
        "agent_notes": []
    }
    
    state = workflow.intake_node(initial_state)
    assert state["student_id"] == "Alice Smith"
    assert state["title"] is not None
    assert state["description"] != ""
    assert state["location"] != "Unknown"  # should extract "Hostel Block A" or similar
    assert state["status"] == "Open"


def test_classification_node() -> None:
    """Test classification returns valid category/priority."""
    state: GraphState = {
        "raw_message": "Wi-Fi not working in Hostel Block A",
        "telegram_id": "987654321",
        "student_id": "Alice Smith",
        "ticket_id": None,
        "title": "Wi-Fi Connection Issue",
        "description": "Wi-Fi not working in Hostel Block A",
        "category": None,
        "location": "Hostel Block A",
        "priority": None,
        "assigned_dept": None,
        "sla_deadline": None,
        "status": "Open",
        "created_at": None,
        "agent_notes": []
    }

    state = workflow.classification_node(state)
    assert state["category"] in constants.CATEGORIES
    assert state["priority"] in constants.PRIORITIES


def test_intake_node(monkeypatch, isolated_db):
    monkeypatch.setattr(
        "backend.workflow.call_gemini",
        lambda prompt, response_schema=None: {
            "title": "Test Title",
            "description": "Test Desc",
            "location": "Block A",
        },
    )

    # Ensure the user exists so the DB lookup inside intake_node succeeds.
    db.create_user(UserCreate(name="Test Student", role="student", telegram_id="9999"))

    state = _base_state(raw_message="Wi-Fi is not working in Block A", telegram_id="9999")
    result = intake_node(state)

    assert result["title"] == "Test Title"
    assert result["description"] == "Test Desc"
    assert result["location"] == "Block A"
    assert result["status"] == "Open"


# ── work_order_node ────────────────────────────────────────────────────


def test_work_order_node(monkeypatch, isolated_db):
    # Create user so the FK constraint on tickets.telegram_id is satisfied.
    db.create_user(UserCreate(name="Test Student", role="student", telegram_id="9999"))

    monkeypatch.setattr(
        "backend.telegram_helpers.format_ticket_reply",
        lambda **kwargs: "Ticket confirmation message",
    )

    state = _base_state(
        raw_message="Wi-Fi down in Block A",
        telegram_id="9999",
        student_id="Test Student",
        title="Wi-Fi Down",
        description="Wi-Fi is not working in Block A",
        category="IT & Wi-Fi",
        location="Block A",
        priority="High",
        assigned_dept="IT Department",
        sla_deadline="2026-06-08T16:00:00",
        status="Open",
        created_at="2026-06-08T12:00:00",
        agent_notes=["Ingested.", "Classified.", "Routed.", "SLA set."],
    )

    result = work_order_node(state)
    assert result["ticket_id"] is not None
    assert result["ticket_id"] > 0
