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


def test_routing_node() -> None:
    """Test routing returns correct department."""
    state: GraphState = {
        "raw_message": "Wi-Fi not working in Hostel Block A",
        "telegram_id": "987654321",
        "student_id": "Alice Smith",
        "ticket_id": None,
        "title": "Wi-Fi Connection Issue",
        "description": "Wi-Fi not working in Hostel Block A",
        "category": "IT & Wi-Fi",
        "location": "Hostel Block A",
        "priority": "High",
        "assigned_dept": None,
        "sla_deadline": None,
        "status": "Open",
        "created_at": None,
        "agent_notes": []
    }

    state = workflow.routing_node(state)
    assert state["assigned_dept"] == "IT Department"


def test_sla_node() -> None:
    """Test SLA deadline calculation."""
    state: GraphState = {
        "raw_message": "Wi-Fi not working in Hostel Block A",
        "telegram_id": "987654321",
        "student_id": "Alice Smith",
        "ticket_id": None,
        "title": "Wi-Fi Connection Issue",
        "description": "Wi-Fi not working in Hostel Block A",
        "category": "IT & Wi-Fi",
        "location": "Hostel Block A",
        "priority": "High",
        "assigned_dept": "IT Department",
        "sla_deadline": None,
        "status": "Open",
        "created_at": None,
        "agent_notes": []
    }

    state = workflow.sla_node(state)
    assert state["sla_deadline"] is not None


def test_full_workflow() -> None:
    """Test complete workflow end-to-end."""
    final_state = workflow.run_workflow(
        raw_message="No water in Room 204 of Hostel 3",
        telegram_id="987654321"
    )

    assert final_state["student_id"] == "Alice Smith"
    assert final_state["title"] is not None
    assert final_state["category"] in constants.CATEGORIES
    assert final_state["priority"] in constants.PRIORITIES
    assert final_state["assigned_dept"] is not None
    assert final_state["sla_deadline"] is not None

    # Verify that the ticket was created in the database
    with db.get_connection() as conn:
        row = conn.execute("SELECT * FROM tickets ORDER BY ticket_id DESC LIMIT 1").fetchone()
        assert row is not None
        ticket = dict(row)
        assert ticket["title"] == final_state["title"]
        assert ticket["category"] == final_state["category"]
        assert ticket["status"] == "Open"

        # Verify notifications were created
        notifications = conn.execute("SELECT * FROM notifications WHERE ticket_id = ?", (ticket["ticket_id"],)).fetchall()
        assert len(notifications) > 0
        assert notifications[0]["recipient"] == "987654321"

