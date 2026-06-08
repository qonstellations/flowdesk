"""Escalation engine script for FlowDesk.

Finds overdue tickets that have breached their SLA deadlines
and escalates them to the appropriate authority.
"""

from __future__ import annotations

from backend import db
from backend.models import EventCreate, NotificationCreate, TicketUpdate


# ── Escalation logic ──────────────────────────────────────────────────


def check_and_escalate() -> int:
    """Find overdue tickets, escalate them, and return the count."""
    overdue_tickets = db.get_overdue_tickets()

    if not overdue_tickets:
        print("  ℹ️  No overdue tickets found")
        return 0

    escalated_count = 0
    for ticket in overdue_tickets:
        ticket_id: int = ticket["ticket_id"]

        # 1. Update ticket status to Escalated
        db.update_ticket(ticket_id, TicketUpdate(status="Escalated"))

        # 2. Log an audit-trail event
        db.create_event(
            EventCreate(
                ticket_id=ticket_id,
                actor_type="system",
                actor_name="Escalation Engine",
                action="ESCALATED",
                details=f"SLA deadline {ticket['sla_deadline']} breached",
            )
        )

        # 3. Queue a notification to the ticket creator
        db.create_notification(
            NotificationCreate(
                ticket_id=ticket_id,
                recipient=ticket["telegram_id"],
                channel="telegram",
                message=(
                    f"⚠️ Ticket #{ticket_id} has been escalated — "
                    f"the SLA deadline ({ticket['sla_deadline']}) was breached."
                ),
                status="pending",
            )
        )

        print(
            f"  🚨 Escalated ticket #{ticket_id}: "
            f"'{ticket['title']}' (deadline was {ticket['sla_deadline']})"
        )
        escalated_count += 1

    return escalated_count


# ── Main ───────────────────────────────────────────────────────────────


def main() -> None:
    """Run escalation check and print results."""
    print("=" * 60)
    print("FlowDesk — Escalation Engine")
    print("=" * 60)

    print("\n🔧 Initialising database …")
    db.init_db()
    print("  ✅ Database initialised\n")

    print("🔍 Checking for overdue tickets …")
    count = check_and_escalate()

    print(f"\n📊 Result: {count} ticket(s) escalated")
    print("=" * 60)


if __name__ == "__main__":
    main()
