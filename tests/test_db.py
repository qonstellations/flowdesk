"""Database tests for FlowDesk.

Tests cover database initialization, CRUD operations for users,
tickets, and events, and verifies that state changes create audit events.
"""

import pytest

# Import from backend.db and backend.models


import os
from pathlib import Path
from backend import db, constants, models

# Override DB path for isolation
constants.DB_PATH = "data/test_flowdesk.db"


def setup_module(module):
    # Ensure test DB is fresh
    db_path = Path(constants.DB_PATH)
    if db_path.exists():
        try:
            db_path.unlink()
        except Exception:
            pass


def teardown_module(module):
    db_path = Path(constants.DB_PATH)
    if db_path.exists():
        try:
            db_path.unlink()
        except Exception:
            pass


def test_init_db() -> None:
    """Test database initialization creates tables."""
    db.init_db()
    # Check if database file exists
    assert Path(constants.DB_PATH).exists()


def test_create_user() -> None:
    """Test user creation."""
    user = models.UserCreate(
        name="John Doe",
        role="student",
        telegram_id="123456789",
        department=None
    )
    user_id = db.create_user(user)
    assert user_id > 0

    fetched = db.get_user_by_telegram_id("123456789")
    assert fetched is not None
    assert fetched["name"] == "John Doe"
    assert fetched["role"] == "student"


def test_create_ticket() -> None:
    """Test ticket creation."""
    ticket = models.TicketCreate(
        telegram_id="123456789",
        title="Wi-Fi Router Broken",
        description="Router is broken in Hostel Block C",
        raw_message="wifi broken",
        category="IT & Wi-Fi",
        location="Hostel Block C",
        priority="High"
    )
    ticket_id = db.create_ticket(ticket)
    assert ticket_id > 0

    fetched = db.get_ticket(ticket_id)
    assert fetched is not None
    assert fetched["title"] == "Wi-Fi Router Broken"
    assert fetched["category"] == "IT & Wi-Fi"
    assert fetched["priority"] == "High"
    assert fetched["status"] == "Open"


def test_create_event() -> None:
    """Test event creation."""
    # Create an event manually for a ticket
    event = models.EventCreate(
        ticket_id=1,
        actor_type="system",
        actor_name="System",
        action="TEST_ACTION",
        details="Manual test event details"
    )
    event_id = db.create_event(event)
    assert event_id > 0


def test_get_ticket() -> None:
    """Test ticket retrieval."""
    ticket = db.get_ticket(1)
    assert ticket is not None
    assert ticket["ticket_id"] == 1


def test_update_ticket_creates_event() -> None:
    """Test that updating a ticket creates an event."""
    ticket = models.TicketCreate(
        telegram_id="123456789",
        title="Mess Water Issue",
        description="No drinking water in Mess Hall",
        raw_message="no water in mess",
        category="Mess & Food",
        location="Mess Hall",
        priority="Medium"
    )
    ticket_id = db.create_ticket(ticket)

    update = models.TicketUpdate(
        status="In Progress",
        assigned_dept="Mess Committee"
    )
    db.update_ticket(ticket_id, update)

    # Check if ticket details are updated
    updated_ticket = db.get_ticket(ticket_id)
    assert updated_ticket["status"] == "In Progress"
    assert updated_ticket["assigned_dept"] == "Mess Committee"

    # Check that events were generated in the audit trail
    with db.get_connection() as conn:
        events = conn.execute(
            "SELECT * FROM events WHERE ticket_id = ? ORDER BY created_at DESC",
            (ticket_id,)
        ).fetchall()
        
        event_actions = [e["action"] for e in events]
        assert "STATUS_UPDATED" in event_actions

