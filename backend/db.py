"""SQLite database access layer for FlowDesk."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from backend import constants
from backend.models import EventCreate, NotificationCreate, TicketCreate, TicketUpdate, UserCreate


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_connection() -> sqlite3.Connection:
    db_path = Path(constants.DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    """Create and migrate all MVP tables idempotently."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                telegram_id TEXT UNIQUE NOT NULL,
                department TEXT,
                verified_email TEXT,
                google_sub TEXT,
                is_verified INTEGER NOT NULL DEFAULT 0,
                linked_at TEXT,
                created_at TEXT NOT NULL
            )
        """)
        _add_column(conn, "users", "verified_email", "TEXT")
        _add_column(conn, "users", "google_sub", "TEXT")
        _add_column(conn, "users", "is_verified", "INTEGER NOT NULL DEFAULT 0")
        _add_column(conn, "users", "linked_at", "TEXT")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS departments (
                department_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL DEFAULT 'General',
                responsibilities TEXT NOT NULL DEFAULT '',
                contact TEXT NOT NULL DEFAULT '',
                escalation_contact TEXT,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        _add_column(conn, "departments", "responsibilities", "TEXT NOT NULL DEFAULT ''")
        _add_column(conn, "departments", "contact", "TEXT NOT NULL DEFAULT ''")
        _add_column(conn, "departments", "active", "INTEGER NOT NULL DEFAULT 1")
        _add_column(conn, "departments", "created_at", "TEXT")
        _add_column(conn, "departments", "updated_at", "TEXT")
        _drop_column_if_exists(conn, "departments", "description")
        _drop_column_if_exists(conn, "departments", "default_target_hours")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                raw_message TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'General',
                location TEXT NOT NULL DEFAULT 'Unknown',
                priority TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Open',
                assigned_dept TEXT,
                department_id INTEGER,
                routing_reason TEXT,
                routing_confidence REAL,
                target_resolution_at TEXT,
                sla_deadline TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                resolved_at TEXT,
                closed_at TEXT,
                FOREIGN KEY (telegram_id) REFERENCES users(telegram_id),
                FOREIGN KEY (department_id) REFERENCES departments(department_id)
            )
        """)
        _add_column(conn, "tickets", "department_id", "INTEGER")
        _add_column(conn, "tickets", "routing_reason", "TEXT")
        _add_column(conn, "tickets", "routing_confidence", "REAL")
        _add_column(conn, "tickets", "target_resolution_at", "TEXT")
        _add_column(conn, "tickets", "admin_approved", "INTEGER NOT NULL DEFAULT 0")
        _add_column(conn, "tickets", "validation_token", "TEXT")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS complaint_drafts (
                draft_id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id TEXT NOT NULL UNIQUE,
                chat_id TEXT NOT NULL,
                draft_complaint TEXT NOT NULL,
                missing_fields TEXT NOT NULL DEFAULT '[]',
                asked_questions TEXT NOT NULL DEFAULT '[]',
                answers TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS link_tokens (
                token TEXT PRIMARY KEY,
                telegram_id TEXT NOT NULL,
                chat_id TEXT NOT NULL,
                user_name TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                used_at TEXT
            )
        """)

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
        conn.commit()


def _add_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _drop_column_if_exists(conn: sqlite3.Connection, table: str, column: str) -> None:
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
    if column not in columns:
        return
    try:
        conn.execute(f"ALTER TABLE {table} DROP COLUMN {column}")
    except sqlite3.OperationalError:
        # Older SQLite versions cannot drop columns. Runtime code no longer reads or writes them.
        pass


def create_user(user: UserCreate) -> int:
    now = utc_now()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (
                name, role, telegram_id, department, verified_email, google_sub,
                is_verified, linked_at, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user.name,
            user.role,
            user.telegram_id,
            user.department,
            user.verified_email,
            user.google_sub,
            1 if user.is_verified else 0,
            now if user.is_verified else None,
            now,
        ))
        conn.commit()
        return int(cursor.lastrowid)


def upsert_telegram_user(telegram_id: str, name: str, role: str = "student") -> dict:
    existing = get_user_by_telegram_id(telegram_id)
    if existing:
        return existing
    create_user(UserCreate(name=name or "Student", role=role, telegram_id=telegram_id))
    return get_user_by_telegram_id(telegram_id) or {}


def get_user_by_telegram_id(telegram_id: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)).fetchone()
        return dict(row) if row else None


def get_user_by_email(email: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE lower(verified_email) = lower(?)", (email,)).fetchone()
        return dict(row) if row else None


def create_pending_google_user(email: str, name: str = "", google_sub: str = "") -> dict:
    existing = get_user_by_email(email)
    if existing:
        return existing

    placeholder_telegram_id = f"google:{email.strip().lower()}"
    create_user(UserCreate(
        name=name or email,
        role="student",
        telegram_id=placeholder_telegram_id,
        verified_email=email.strip().lower(),
        google_sub=google_sub,
        is_verified=True,
    ))
    return get_user_by_email(email) or {}


def link_verified_user(telegram_id: str, name: str, email: str, google_sub: str) -> None:
    now = utc_now()
    with get_connection() as conn:
        email_row = conn.execute(
            "SELECT * FROM users WHERE lower(verified_email) = lower(?)",
            (email,),
        ).fetchone()
        if email_row and email_row["telegram_id"] != telegram_id:
            conn.execute("""
                DELETE FROM users
                WHERE telegram_id = ?
                  AND verified_email IS NULL
                  AND NOT EXISTS (
                      SELECT 1 FROM tickets WHERE tickets.telegram_id = users.telegram_id
                  )
            """, (telegram_id,))
            conn.execute("""
                UPDATE users
                SET name = ?, role = 'student', telegram_id = ?, verified_email = ?,
                    google_sub = ?, is_verified = 1, linked_at = ?
                WHERE user_id = ?
            """, (name or email, telegram_id, email, google_sub, now, email_row["user_id"]))
        else:
            conn.execute("""
                INSERT INTO users (
                    name, role, telegram_id, verified_email, google_sub, is_verified,
                    linked_at, created_at
                )
                VALUES (?, 'student', ?, ?, ?, 1, ?, ?)
                ON CONFLICT(telegram_id) DO UPDATE SET
                    name = excluded.name,
                    role = 'student',
                    verified_email = excluded.verified_email,
                    google_sub = excluded.google_sub,
                    is_verified = 1,
                    linked_at = excluded.linked_at
            """, (name or email, telegram_id, email, google_sub, now, now))
        conn.commit()


def create_ticket(ticket: TicketCreate) -> int:
    now = utc_now()
    user = get_user_by_telegram_id(ticket.telegram_id)
    actor_name = user["name"] if user else "Unknown User"
    actor_type = user["role"] if user else "student"
    assigned_dept = get_department_name(ticket.department_id) if ticket.department_id else None
    deadline = ticket.target_resolution_at

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tickets (
                telegram_id, title, description, raw_message, category, location,
                priority, status, assigned_dept, department_id, routing_reason,
                routing_confidence, target_resolution_at, sla_deadline, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Open', ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ticket.telegram_id,
            ticket.title,
            ticket.description,
            ticket.raw_message,
            ticket.category,
            ticket.location,
            ticket.priority,
            assigned_dept,
            ticket.department_id,
            ticket.routing_reason,
            ticket.routing_confidence,
            ticket.target_resolution_at,
            deadline,
            now,
            now,
        ))
        ticket_id = int(cursor.lastrowid)
        cursor.execute("""
            INSERT INTO events (ticket_id, actor_type, actor_name, action, details, created_at)
            VALUES (?, ?, ?, 'TICKET_CREATED', ?, ?)
        """, (ticket_id, actor_type, actor_name, f"Ticket created: {ticket.title}", now))
        conn.commit()
        return ticket_id


def get_ticket(ticket_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute("""
            SELECT t.*, d.name AS department_name
            FROM tickets t
            LEFT JOIN departments d ON d.department_id = t.department_id
            WHERE t.ticket_id = ?
        """, (ticket_id,)).fetchone()
        return dict(row) if row else None


def get_tickets_by_telegram_id(telegram_id: str) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT t.*, d.name AS department_name
            FROM tickets t
            LEFT JOIN departments d ON d.department_id = t.department_id
            WHERE t.telegram_id = ?
            ORDER BY t.created_at DESC
        """, (telegram_id,)).fetchall()
        return [dict(row) for row in rows]


def get_tickets_by_verified_email(email: str) -> list[dict]:
    user = get_user_by_email(email)
    if not user:
        return []
    return get_tickets_by_telegram_id(user["telegram_id"])


def get_all_tickets() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT t.*, d.name AS department_name
            FROM tickets t
            LEFT JOIN departments d ON d.department_id = t.department_id
            ORDER BY t.created_at DESC
        """).fetchall()
        return [dict(row) for row in rows]


def get_tickets_by_status(status: str) -> list[dict]:
    return [ticket for ticket in get_all_tickets() if ticket.get("status") == status]


def get_tickets_by_department(department: str) -> list[dict]:
    return [
        ticket for ticket in get_all_tickets()
        if (ticket.get("department_name") or ticket.get("assigned_dept")) == department
    ]


def update_ticket(ticket_id: int, update: TicketUpdate) -> None:
    current = get_ticket(ticket_id)
    if not current:
        raise ValueError(f"Ticket with ID {ticket_id} does not exist.")

    now = utc_now()
    fields: list[str] = []
    params: list[Any] = []
    events: list[dict[str, str]] = []

    def set_field(column: str, value: Any, action: str | None = None, details: str | None = None) -> None:
        if value is None or value == current.get(column):
            return
        fields.append(f"{column} = ?")
        params.append(value)
        if action:
            events.append({"action": action, "details": details or f"{column} updated"})

    if update.status is not None and update.status != current["status"]:
        set_field("status", update.status)
        action = {
            "Resolved": "RESOLVED",
            "Closed": "CLOSED",
            "Escalated": "ESCALATED",
            "Reopened": "REOPENED",
        }.get(update.status, "STATUS_UPDATED")
        events.append({"action": action, "details": f"Status changed from {current['status']} to {update.status}"})

    if update.department_id is not None and update.department_id != current.get("department_id"):
        dept_name = get_department_name(update.department_id)
        set_field("department_id", update.department_id)
        set_field("assigned_dept", dept_name)
        events.append({"action": "ROUTED", "details": f"Assigned department set to {dept_name}"})
    elif update.assigned_dept is not None:
        set_field("assigned_dept", update.assigned_dept, "ROUTED", f"Assigned department set to {update.assigned_dept}")

    set_field("routing_reason", update.routing_reason)
    set_field("routing_confidence", update.routing_confidence)
    if update.target_resolution_at is not None:
        set_field("target_resolution_at", update.target_resolution_at, "TARGET_RESOLUTION_SET", f"Target resolution set to {update.target_resolution_at}")
        set_field("sla_deadline", update.target_resolution_at)
    elif update.sla_deadline is not None:
        set_field("sla_deadline", update.sla_deadline, "TARGET_RESOLUTION_SET", f"Target resolution set to {update.sla_deadline}")

    set_field("resolved_at", update.resolved_at)
    set_field("closed_at", update.closed_at)

    # ── Email flow integration (connected to frontend logic) ──────────────────
    validation_token_to_send = None
    status_is_assigned_or_escalated = (update.status in ("Assigned", "Escalated")) or (update.status is None and current.get("status") in ("Assigned", "Escalated"))
    dept_is_changing = (update.department_id is not None and update.department_id != current.get("department_id"))
    
    if (update.status in ("Assigned", "Escalated") and current.get("status") not in ("Assigned", "Escalated")) or (status_is_assigned_or_escalated and dept_is_changing):
        import secrets
        validation_token_to_send = secrets.token_urlsafe(24)
        fields.append("admin_approved = ?")
        params.append(1)
        fields.append("validation_token = ?")
        params.append(validation_token_to_send)
        events.append({"action": "ADMIN_APPROVED", "details": "Ticket approved by admin. Email queued/sent to department."})
    elif update.status == "Rejected" and current.get("status") != "Rejected":
        fields.append("admin_approved = ?")
        params.append(-1)
        fields.append("validation_token = ?")
        params.append(None)
        events.append({"action": "ADMIN_REJECTED", "details": "Ticket rejected/validation failed by admin."})

    if not fields:
        return

    fields.append("updated_at = ?")
    params.extend([now, ticket_id])

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE tickets SET {', '.join(fields)} WHERE ticket_id = ?", tuple(params))
        for event in events:
            cursor.execute("""
                INSERT INTO events (ticket_id, actor_type, actor_name, action, details, created_at)
                VALUES (?, 'system', 'System', ?, ?, ?)
            """, (ticket_id, event["action"], event["details"], now))
        conn.commit()

    if validation_token_to_send:
        try:
            import backend.email_service as email_service
            updated_ticket = get_ticket(ticket_id)
            if updated_ticket:
                email_service.send_department_completion_link(updated_ticket, validation_token_to_send)
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception(f"Failed to send email inside update_ticket: {e}")


def create_event(event: EventCreate) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO events (ticket_id, actor_type, actor_name, action, details, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (event.ticket_id, event.actor_type, event.actor_name, event.action, event.details, utc_now()))
        conn.commit()
        return int(cursor.lastrowid)


def get_events_by_ticket(ticket_id: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM events WHERE ticket_id = ? ORDER BY created_at ASC",
            (ticket_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def get_overdue_tickets() -> list[dict]:
    now = utc_now()
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM tickets
            WHERE status NOT IN ('Resolved', 'Closed')
              AND COALESCE(target_resolution_at, sla_deadline) IS NOT NULL
              AND COALESCE(target_resolution_at, sla_deadline) < ?
        """, (now,)).fetchall()
        return [dict(row) for row in rows]


def create_notification(notification: NotificationCreate) -> int:
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
            utc_now(),
        ))
        conn.commit()
        return int(cursor.lastrowid)


def get_departments(include_inactive: bool = True) -> list[dict]:
    query = "SELECT * FROM departments"
    if not include_inactive:
        query += " WHERE active = 1"
    query += " ORDER BY active DESC, name ASC"
    with get_connection() as conn:
        rows = conn.execute(query).fetchall()
        return [dict(row) for row in rows]


def get_active_departments() -> list[dict]:
    return get_departments(include_inactive=False)


def get_department(department_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM departments WHERE department_id = ?", (department_id,)).fetchone()
        return dict(row) if row else None


def get_department_name(department_id: int | None) -> str | None:
    if department_id is None:
        return None
    dept = get_department(department_id)
    return dept["name"] if dept else None


def create_department(
    name: str,
    responsibilities: str,
    contact: str,
    escalation_contact: str,
) -> int:
    now = utc_now()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO departments (
                name, category, responsibilities, contact, escalation_contact,
                active, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, 1, ?, ?)
        """, (
            name,
            name,
            responsibilities,
            contact,
            escalation_contact,
            now,
            now,
        ))
        conn.commit()
        return int(cursor.lastrowid)


def update_department(
    department_id: int,
    name: str,
    responsibilities: str,
    contact: str,
    escalation_contact: str,
    active: bool,
) -> None:
    with get_connection() as conn:
        conn.execute("""
            UPDATE departments
            SET name = ?, category = ?, responsibilities = ?,
                contact = ?, escalation_contact = ?, active = ?, updated_at = ?
            WHERE department_id = ?
        """, (
            name,
            name,
            responsibilities,
            contact,
            escalation_contact,
            1 if active else 0,
            utc_now(),
            department_id,
        ))
        conn.commit()


def upsert_complaint_draft(
    telegram_id: str,
    chat_id: str,
    draft_complaint: str,
    missing_fields: list[str],
    asked_questions: list[str],
    answers: list[str],
    ttl_minutes: int = 60,
) -> None:
    now_dt = datetime.now(timezone.utc)
    now = now_dt.isoformat()
    expires_at = (now_dt + timedelta(minutes=ttl_minutes)).isoformat()
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO complaint_drafts (
                telegram_id, chat_id, draft_complaint, missing_fields,
                asked_questions, answers, created_at, updated_at, expires_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                chat_id = excluded.chat_id,
                draft_complaint = excluded.draft_complaint,
                missing_fields = excluded.missing_fields,
                asked_questions = excluded.asked_questions,
                answers = excluded.answers,
                updated_at = excluded.updated_at,
                expires_at = excluded.expires_at
        """, (
            telegram_id,
            chat_id,
            draft_complaint,
            json.dumps(missing_fields),
            json.dumps(asked_questions),
            json.dumps(answers),
            now,
            now,
            expires_at,
        ))
        conn.commit()


def get_active_complaint_draft(telegram_id: str) -> dict | None:
    now = utc_now()
    with get_connection() as conn:
        row = conn.execute("""
            SELECT * FROM complaint_drafts
            WHERE telegram_id = ? AND expires_at > ?
        """, (telegram_id, now)).fetchone()
        if not row:
            return None
        draft = dict(row)
        for key in ("missing_fields", "asked_questions", "answers"):
            draft[key] = json.loads(draft.get(key) or "[]")
        return draft


def delete_complaint_draft(telegram_id: str) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM complaint_drafts WHERE telegram_id = ?", (telegram_id,))
        conn.commit()


def create_link_token(token: str, telegram_id: str, chat_id: str, user_name: str, ttl_minutes: int = 15) -> None:
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)).isoformat()
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO link_tokens (token, telegram_id, chat_id, user_name, expires_at)
            VALUES (?, ?, ?, ?, ?)
        """, (token, telegram_id, chat_id, user_name, expires_at))
        conn.commit()


def consume_link_token(token: str) -> dict | None:
    now = utc_now()
    with get_connection() as conn:
        row = conn.execute("""
            SELECT * FROM link_tokens
            WHERE token = ? AND used_at IS NULL AND expires_at > ?
        """, (token, now)).fetchone()
        if not row:
            return None
        conn.execute("UPDATE link_tokens SET used_at = ? WHERE token = ?", (now, token))
        conn.commit()
        return dict(row)


def set_ticket_validation(ticket_id: int, admin_approved: int, validation_token: str | None = None) -> None:
    now = utc_now()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE tickets
            SET admin_approved = ?, validation_token = ?, updated_at = ?
            WHERE ticket_id = ?
        """, (admin_approved, validation_token, now, ticket_id))
        
        # Add audit trail event
        action = "ADMIN_APPROVED" if admin_approved == 1 else "ADMIN_REJECTED"
        details = (
            "Ticket approved by admin. Email queued/sent to department."
            if admin_approved == 1
            else "Ticket rejected/validation failed by admin."
        )
        cursor.execute("""
            INSERT INTO events (ticket_id, actor_type, actor_name, action, details, created_at)
            VALUES (?, 'admin', 'Admin', ?, ?, ?)
        """, (ticket_id, action, details, now))
        conn.commit()


def get_ticket_by_validation_token(token: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute("""
            SELECT t.*, d.name AS department_name, d.escalation_contact AS department_email
            FROM tickets t
            LEFT JOIN departments d ON d.department_id = t.department_id
            WHERE t.validation_token = ?
        """, (token,)).fetchone()
        return dict(row) if row else None


def resolve_ticket_by_token(ticket_id: int) -> None:
    now = utc_now()
    with get_connection() as conn:
        cursor = conn.cursor()
        # Mark ticket as resolved
        cursor.execute("""
            UPDATE tickets
            SET status = 'Resolved', resolved_at = ?, validation_token = NULL, updated_at = ?
            WHERE ticket_id = ?
        """, (now, now, ticket_id))
        
        # Create event
        cursor.execute("""
            INSERT INTO events (ticket_id, actor_type, actor_name, action, details, created_at)
            VALUES (?, 'system', 'System', 'RESOLVED', 'Ticket marked resolved via secure email link.', ?)
        """, (ticket_id, now))
        conn.commit()


