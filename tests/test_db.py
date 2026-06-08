"""Database CRUD tests for the FlowDesk data layer."""
from __future__ import annotations

import sqlite3

import pytest

import backend.db as db
from backend.models import EventCreate, TicketCreate, TicketUpdate, UserCreate


# ── Helper ─────────────────────────────────────────────────────────────


def _make_user(telegram_id: str = "5001", name: str = "Alice") -> int:
    """Shortcut: create a user and return the user_id."""
    return db.create_user(
        UserCreate(name=name, role="student", telegram_id=telegram_id)
    )


def _make_ticket(telegram_id: str = "5001") -> int:
    """Shortcut: create a ticket and return the ticket_id."""
    return db.create_ticket(
        TicketCreate(
            telegram_id=telegram_id,
            title="Test Ticket",
            description="Desc",
            raw_message="raw",
            category="IT & Wi-Fi",
            priority="High",
            location="Lab 1",
        )
    )


# ── Tests ──────────────────────────────────────────────────────────────


def test_init_db(isolated_db):
    """After init_db (run by the fixture), all 6 departments should exist."""
    departments = db.get_departments()
    assert len(departments) == 6


def test_create_user(isolated_db):
    user_id = _make_user()
    assert user_id > 0

    user = db.get_user_by_telegram_id("5001")
    assert user is not None
    assert user["name"] == "Alice"


def test_create_user_duplicate_telegram_id(isolated_db):
    _make_user(telegram_id="6001")
    with pytest.raises(sqlite3.IntegrityError):
        _make_user(telegram_id="6001", name="Bob")


def test_create_ticket(isolated_db):
    _make_user(telegram_id="5002")
    ticket_id = _make_ticket(telegram_id="5002")
    assert ticket_id > 0


def test_get_ticket(isolated_db):
    _make_user(telegram_id="5002")
    ticket_id = _make_ticket(telegram_id="5002")

    ticket = db.get_ticket(ticket_id)
    assert ticket is not None
    assert ticket["title"] == "Test Ticket"
    assert ticket["category"] == "IT & Wi-Fi"
    assert ticket["priority"] == "High"
    assert ticket["status"] == "Open"


def test_create_event(isolated_db):
    _make_user(telegram_id="5002")
    ticket_id = _make_ticket(telegram_id="5002")

    event_id = db.create_event(
        EventCreate(
            ticket_id=ticket_id,
            actor_type="system",
            actor_name="Test",
            action="CLASSIFIED",
            details="Test details",
        )
    )
    assert event_id > 0


def test_get_events_by_ticket(isolated_db):
    """create_ticket auto-creates 1 TICKET_CREATED event; adding 2 more → ≥ 3."""
    _make_user(telegram_id="5002")
    ticket_id = _make_ticket(telegram_id="5002")

    db.create_event(
        EventCreate(
            ticket_id=ticket_id,
            actor_type="system",
            actor_name="Test",
            action="CLASSIFIED",
            details="d1",
        )
    )
    db.create_event(
        EventCreate(
            ticket_id=ticket_id,
            actor_type="system",
            actor_name="Test",
            action="ROUTED",
            details="d2",
        )
    )

    events = db.get_events_by_ticket(ticket_id)
    assert len(events) >= 3


def test_update_ticket_creates_event(isolated_db):
    _make_user(telegram_id="5002")
    ticket_id = _make_ticket(telegram_id="5002")

    events_before = db.get_events_by_ticket(ticket_id)
    db.update_ticket(ticket_id, TicketUpdate(status="Assigned"))
    events_after = db.get_events_by_ticket(ticket_id)

    assert len(events_after) > len(events_before)


def test_get_tickets_by_status(isolated_db):
    _make_user(telegram_id="5002")
    _make_ticket(telegram_id="5002")

    open_tickets = db.get_tickets_by_status("Open")
    assert len(open_tickets) >= 1


def test_get_all_tickets(isolated_db):
    _make_user(telegram_id="5002")
    _make_ticket(telegram_id="5002")
    _make_ticket(telegram_id="5002")

    all_tickets = db.get_all_tickets()
    assert len(all_tickets) >= 2
