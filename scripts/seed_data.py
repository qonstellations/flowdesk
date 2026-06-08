"""Demo data seeding script for FlowDesk.

Populates the database with sample users, departments, and tickets
so the system can be demonstrated without manual data entry.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from backend import db
from backend import constants
from backend.models import TicketCreate, TicketUpdate, UserCreate
from backend.router import route_ticket
from backend.sla import calculate_sla_deadline


# ── Users ──────────────────────────────────────────────────────────────


def seed_users() -> None:
    """Create demo students, staff, and admins."""
    users = [
        # Students
        UserCreate(name="Aarav Sharma", telegram_id="1001", role="student"),
        UserCreate(name="Priya Patel", telegram_id="1002", role="student"),
        UserCreate(name="Rohan Gupta", telegram_id="1003", role="student"),
        # Staff
        UserCreate(
            name="Vikram Singh",
            telegram_id="2001",
            role="staff",
            department="IT Department",
        ),
        UserCreate(
            name="Meera Nair",
            telegram_id="2002",
            role="staff",
            department="Hostel Maintenance Team",
        ),
        # Admin
        UserCreate(
            name="Dr. Anand Kulkarni",
            telegram_id="3001",
            role="admin",
            department="General Admin",
        ),
    ]

    for user in users:
        try:
            user_id = db.create_user(user)
            print(f"  ✅ Created user '{user.name}' (ID {user_id})")
        except sqlite3.IntegrityError:
            print(f"  ⏭️  User '{user.name}' already exists — skipped")


# ── Departments ────────────────────────────────────────────────────────


def seed_departments() -> None:
    """Ensure departments exist (may be handled by db init)."""
    print("  ℹ️  Departments are seeded automatically by db.init_db()")


# ── Tickets ────────────────────────────────────────────────────────────


def seed_tickets() -> None:
    """Create sample tickets across categories."""
    now = datetime.now(timezone.utc).isoformat()

    tickets = [
        TicketCreate(
            telegram_id="1001",
            title="Wi-Fi Not Working in Hostel Block A",
            description="Students in Hostel Block A are unable to connect to Wi-Fi since last night.",
            raw_message="The Wi-Fi in Block A is completely down, we can't attend online classes.",
            category="IT & Wi-Fi",
            priority="High",
            location="Hostel Block A",
        ),
        TicketCreate(
            telegram_id="1002",
            title="Water Leakage in Room 204",
            description="Severe water leakage from the ceiling in Room 204, Block B, causing damage to belongings.",
            raw_message="There is serious water leaking from the ceiling in my room 204, block B.",
            category="Hostel Maintenance",
            priority="Critical",
            location="Room 204, Block B",
        ),
        TicketCreate(
            telegram_id="1003",
            title="Poor Food Quality in North Mess",
            description="Multiple students complaining about poor food quality and hygiene issues in North Mess.",
            raw_message="The food quality in North Mess has been terrible, found stale chapatis today.",
            category="Mess & Food",
            priority="Medium",
            location="North Mess",
        ),
        TicketCreate(
            telegram_id="1001",
            title="Broken Bench Near Library",
            description="A bench near the Central Library entrance is broken and poses a safety hazard.",
            raw_message="There is a broken bench near the library, someone could get hurt.",
            category="Campus Maintenance",
            priority="Low",
            location="Central Library Area",
        ),
        TicketCreate(
            telegram_id="1002",
            title="Course Registration Portal Down",
            description="The course registration portal has been inaccessible since this morning, blocking enrolments.",
            raw_message="Course registration portal is not loading at all, can't register for courses.",
            category="Academics",
            priority="High",
            location="Unknown",
        ),
    ]

    for ticket_data in tickets:
        ticket_id = db.create_ticket(ticket_data)

        # Route to the correct department
        dept = route_ticket(ticket_data.category)
        # Compute SLA deadline from priority and creation time
        deadline = calculate_sla_deadline(ticket_data.priority, now)

        db.update_ticket(
            ticket_id,
            TicketUpdate(assigned_dept=dept, sla_deadline=deadline),
        )
        print(
            f"  🎫 Ticket #{ticket_id}: '{ticket_data.title}' "
            f"→ {dept} (SLA: {deadline})"
        )


# ── Main ───────────────────────────────────────────────────────────────


def main() -> None:
    """Run all seed functions."""
    print("=" * 60)
    print("FlowDesk — Seeding demo data")
    print("=" * 60)

    print("\n🔧 Initialising database …")
    db.init_db()
    print("  ✅ Database initialised\n")

    print("👤 Seeding users …")
    seed_users()

    print("\n🏢 Seeding departments …")
    seed_departments()

    print("\n🎫 Seeding tickets …")
    seed_tickets()

    print("\n" + "=" * 60)
    print("✅ Demo data seeded successfully!")
    print("=" * 60)


if __name__ == "__main__":
    seed()
