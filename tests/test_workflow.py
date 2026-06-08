"""Tests for LangGraph workflow nodes."""
from __future__ import annotations

import pytest

import backend.db as db
from backend import constants
from backend.models import GraphState, UserCreate
from backend.workflow import (
    classification_node,
    intake_node,
    routing_node,
    sla_node,
    work_order_node,
)


# ── Helpers ────────────────────────────────────────────────────────────


def _base_state(**overrides) -> dict:
    """Return a fully-populated ``GraphState``-compatible dict.

    Every required key has a sensible default; callers override only the
    keys relevant to their test.
    """
    state: dict = {
        "raw_message": "Test complaint message",
        "telegram_id": "9999",
        "student_id": None,
        "ticket_id": None,
        "title": None,
        "description": "Test description",
        "category": None,
        "location": None,
        "priority": None,
        "assigned_dept": None,
        "sla_deadline": None,
        "status": "Open",
        "created_at": None,
        "agent_notes": [],
    }
    state.update(overrides)
    return state


# ── routing_node ───────────────────────────────────────────────────────


def test_routing_node():
    state = _base_state(category="IT & Wi-Fi")
    result = routing_node(state)
    assert result["assigned_dept"] == "IT Department"


def test_routing_node_unknown_category():
    state = _base_state(category="Unknown Category")
    result = routing_node(state)
    assert result["assigned_dept"] == "General Admin"


# ── sla_node ───────────────────────────────────────────────────────────


def test_sla_node():
    state = _base_state(priority="Critical", created_at="2026-06-08T12:00:00")
    result = sla_node(state)
    assert result["sla_deadline"] == "2026-06-08T16:00:00"


def test_sla_node_generates_created_at():
    state = _base_state(priority="Medium", created_at=None)
    result = sla_node(state)
    assert result["created_at"] is not None
    assert result["sla_deadline"] is not None


# ── classification_node ────────────────────────────────────────────────


def test_classification_node(monkeypatch):
    monkeypatch.setattr(
        "backend.classifier.classify_complaint",
        lambda desc: {"category": "Hostel Maintenance", "priority": "High"},
    )
    state = _base_state(description="The hostel geyser is broken")
    result = classification_node(state)
    assert result["category"] == "Hostel Maintenance"
    assert result["priority"] == "High"


# ── intake_node ────────────────────────────────────────────────────────


def test_intake_node(monkeypatch, isolated_db):
    monkeypatch.setattr(
        "backend.llm.call_gemini",
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
