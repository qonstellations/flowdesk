"""Shared pytest fixtures for the FlowDesk test suite."""
from __future__ import annotations

import pytest

from backend import constants
from backend import db
from backend.models import TicketCreate, UserCreate


@pytest.fixture()
def isolated_db(tmp_path):
    """Redirect all DB operations to a temporary SQLite file.

    Using ``tmp_path`` rather than ``:memory:`` because every call to
    ``db.get_connection()`` opens a *new* connection, and ``:memory:``
    databases are per-connection, so tables would vanish between calls.
    """
    original_db_path = constants.DB_PATH
    constants.DB_PATH = str(tmp_path / "test_flowdesk.db")
    db.init_db()
    yield
    constants.DB_PATH = original_db_path


@pytest.fixture()
def sample_user(isolated_db):
    """Create a test student user and return the ``user_id``."""
    user_id = db.create_user(
        UserCreate(name="Test Student", role="student", telegram_id="9999")
    )
    return user_id


@pytest.fixture()
def sample_ticket(isolated_db, sample_user):
    """Create a test ticket and return the ``ticket_id``."""
    ticket_id = db.create_ticket(
        TicketCreate(
            telegram_id="9999",
            title="Test Issue",
            description="Test description",
            raw_message="test raw message",
            category="IT & Wi-Fi",
            location="Block A",
            priority="High",
        )
    )
    return ticket_id
