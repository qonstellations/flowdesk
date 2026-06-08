"""SQLite database access layer for FlowDesk.

Provides connection management, table initialisation, and CRUD helpers
for users, tickets, events, and notifications.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from backend import constants
from backend.models import (
    EventCreate,
    NotificationCreate,
    TicketCreate,
    TicketUpdate,
    UserCreate,
)


# ── Connection management ──────────────────────────────────────────────


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection to the configured database.

    Uses ``constants.DB_PATH`` and ensures the parent directory exists.
    The connection is configured with ``row_factory = sqlite3.Row`` so
    that rows behave like dicts.
    """
    db_path = Path(constants.DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


# ── Schema bootstrap ──────────────────────────────────────────────────


def init_db() -> None:
    """Create all tables (if they don't exist) and seed departments.

    Tables: users, tickets, events, notifications, departments.
    """
    with get_connection() as conn:
        # 1. Users table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                telegram_id TEXT UNIQUE NOT NULL,
                department TEXT,
                created_at TEXT NOT NULL
            )
        """)
        # 2. Tickets table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                raw_message TEXT NOT NULL,
                category TEXT NOT NULL,
                location TEXT NOT NULL DEFAULT 'Unknown',
                priority TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Open',
                assigned_dept TEXT,
                sla_deadline TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                resolved_at TEXT,
                closed_at TEXT,
                FOREIGN KEY (telegram_id) REFERENCES users(telegram_id)
            )
        """)
        # 3. Events table (Audit Trail)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                actor_type TEXT NOT NULL,
                actor_name TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id)
            )
        """)
        # 4. Departments table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS departments (
                department_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL,
                escalation_contact TEXT
            )
        """)
        # 5. Notifications table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                recipient TEXT NOT NULL,
                channel TEXT NOT NULL,
                message TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id)
            )
        """)

        # Seed departments
        departments_seed = [
            ("IT Department", "IT & Wi-Fi"),
            ("Hostel Maintenance Team", "Hostel Maintenance"),
            ("Campus Facilities Team", "Campus Maintenance"),
            ("Mess Committee", "Mess & Food"),
            ("Academic Office", "Academics"),
            ("General Admin", "Other")
        ]
        for name, category in departments_seed:
            conn.execute("""
                INSERT INTO departments (name, category)
                VALUES (?, ?)
                ON CONFLICT(name) DO NOTHING
            """, (name, category))
        conn.commit()


# ── Users ──────────────────────────────────────────────────────────────


def create_user(user: UserCreate) -> int:
    """Insert a new user and return the generated user ID."""
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (name, role, telegram_id, department, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user.name, user.role, user.telegram_id, user.department, now))
        conn.commit()
        return cursor.lastrowid


def get_user_by_telegram_id(telegram_id: str) -> dict | None:
    """Look up a user by their Telegram ID.

    Returns a dict of user fields, or ``None`` if not found.
    """
    with get_connection() as conn:
        row = conn.execute("""
            SELECT user_id, name, role, telegram_id, department, created_at
            FROM users
            WHERE telegram_id = ?
        """, (telegram_id,)).fetchone()
        return dict(row) if row else None


# ── Tickets ────────────────────────────────────────────────────────────


def create_ticket(ticket: TicketCreate) -> int:
    """Insert a new ticket and return the generated ticket ID."""
    now = datetime.now(timezone.utc).isoformat()
    
    # Try to find user to attribute the creation audit event actor
    user = get_user_by_telegram_id(ticket.telegram_id)
    actor_name = user["name"] if user else "Unknown User"
    actor_type = user["role"] if user else "student"

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tickets (
                telegram_id, title, description, raw_message, category,
                location, priority, status, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ticket.telegram_id,
            ticket.title,
            ticket.description,
            ticket.raw_message,
            ticket.category,
            ticket.location,
            ticket.priority,
            "Open",
            now,
            now
        ))
        ticket_id = cursor.lastrowid

        # Insert audit trail for ticket creation
        cursor.execute("""
            INSERT INTO events (ticket_id, actor_type, actor_name, action, details, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            ticket_id,
            actor_type,
            actor_name,
            "TICKET_CREATED",
            f"Ticket created: {ticket.title}",
            now
        ))
        
        conn.commit()
        return ticket_id


def get_ticket(ticket_id: int) -> dict | None:
    """Fetch a single ticket by ID.

    Returns a dict of ticket fields, or ``None`` if not found.
    """
    with get_connection() as conn:
        row = conn.execute("""
            SELECT * FROM tickets WHERE ticket_id = ?
        """, (ticket_id,)).fetchone()
        return dict(row) if row else None


def get_tickets_by_telegram_id(telegram_id: str) -> list[dict]:
    """Return all tickets filed by the user with the given Telegram ID."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM tickets WHERE telegram_id = ? ORDER BY created_at DESC
        """, (telegram_id,)).fetchall()
        return [dict(row) for row in rows]


def get_all_tickets() -> list[dict]:
    """Return every ticket in the database (admin view)."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM tickets ORDER BY created_at DESC
        """).fetchall()
        return [dict(row) for row in rows]


def get_tickets_by_status(status: str) -> list[dict]:
    """Return all tickets that currently have the given *status*."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM tickets WHERE status = ? ORDER BY created_at DESC
        """, (status,)).fetchall()
        return [dict(row) for row in rows]


def get_tickets_by_department(department: str) -> list[dict]:
    """Return all tickets assigned to *department*."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM tickets WHERE assigned_dept = ? ORDER BY created_at DESC
        """, (department,)).fetchall()
        return [dict(row) for row in rows]


def update_ticket(ticket_id: int, update: TicketUpdate) -> None:
    """Apply a partial update to a ticket and record an audit event.

    Only non-``None`` fields in *update* are written.  A corresponding
    ``EventCreate`` is persisted automatically.
    """
    current = get_ticket(ticket_id)
    if not current:
        raise ValueError(f"Ticket with ID {ticket_id} does not exist.")

    now = datetime.now(timezone.utc).isoformat()
    fields_to_update = []
    params = []
    events_to_create = []

    if update.status is not None and update.status != current["status"]:
        fields_to_update.append("status = ?")
        params.append(update.status)
        
        # Determine specific action
        action = "STATUS_UPDATED"
        if update.status == "Resolved":
            action = "RESOLVED"
        elif update.status == "Closed":
            action = "CLOSED"
        elif update.status == "Escalated":
            action = "ESCALATED"
        elif update.status == "Reopened":
            action = "REOPENED"

        events_to_create.append({
            "action": action,
            "details": f"Status changed from {current['status']} to {update.status}",
            "actor_type": "system",
            "actor_name": "System"
        })

    if update.assigned_dept is not None and update.assigned_dept != current["assigned_dept"]:
        fields_to_update.append("assigned_dept = ?")
        params.append(update.assigned_dept)
        events_to_create.append({
            "action": "ROUTED",
            "details": f"Assigned department set to {update.assigned_dept}",
            "actor_type": "system",
            "actor_name": "System"
        })

    if update.sla_deadline is not None and update.sla_deadline != current["sla_deadline"]:
        fields_to_update.append("sla_deadline = ?")
        params.append(update.sla_deadline)
        events_to_create.append({
            "action": "SLA_ASSIGNED",
            "details": f"SLA deadline set to {update.sla_deadline}",
            "actor_type": "system",
            "actor_name": "System"
        })

    if update.resolved_at is not None:
        fields_to_update.append("resolved_at = ?")
        params.append(update.resolved_at)

    if update.closed_at is not None:
        fields_to_update.append("closed_at = ?")
        params.append(update.closed_at)

    if not fields_to_update:
        return

    fields_to_update.append("updated_at = ?")
    params.append(now)
    
    # Ticket ID in WHERE clause
    params.append(ticket_id)
    
    query = f"UPDATE tickets SET {', '.join(fields_to_update)} WHERE ticket_id = ?"

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, tuple(params))
        
        # Log audit events
        for event in events_to_create:
            cursor.execute("""
                INSERT INTO events (ticket_id, actor_type, actor_name, action, details, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (ticket_id, event["actor_type"], event["actor_name"], event["action"], event["details"], now))
            
        conn.commit()


# ── Events (audit trail) ──────────────────────────────────────────────


def create_event(event: EventCreate) -> int:
    """Insert an audit-trail event and return its generated ID."""
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO events (ticket_id, actor_type, actor_name, action, details, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (event.ticket_id, event.actor_type, event.actor_name, event.action, event.details, now))
        conn.commit()
        return cursor.lastrowid


def get_events_by_ticket(ticket_id: int) -> list[dict]:
    """Return all events associated with *ticket_id*, oldest first."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM events WHERE ticket_id = ? ORDER BY created_at ASC
        """, (ticket_id,)).fetchall()
        return [dict(row) for row in rows]


# ── Escalation helpers ─────────────────────────────────────────────────


def get_overdue_tickets() -> list[dict]:
    """Return tickets whose SLA deadline has passed without resolution.

    Used by the escalation engine to identify tickets that need
    automatic status promotion to ``"Escalated"``.
    """
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM tickets
            WHERE status NOT IN ('Resolved', 'Closed')
              AND sla_deadline IS NOT NULL
              AND sla_deadline < ?
        """, (now,)).fetchall()
        return [dict(row) for row in rows]


# ── Notifications ──────────────────────────────────────────────────────


def create_notification(notification: NotificationCreate) -> int:
    """Queue a notification record and return its generated ID."""
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO notifications (ticket_id, recipient, channel, message, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            notification.ticket_id,
            notification.recipient,
            notification.channel,
            notification.message,
            notification.status,
            now
        ))
        conn.commit()
        return cursor.lastrowid


# ── Departments ────────────────────────────────────────────────────────


def get_departments() -> list[dict]:
    """Return all department records."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM departments
        """).fetchall()
        return [dict(row) for row in rows]
