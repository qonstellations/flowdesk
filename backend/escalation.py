"""Reusable target-resolution escalation logic."""

from __future__ import annotations

from backend import db
from backend.models import NotificationCreate, TicketUpdate


def escalate_overdue_tickets() -> int:
    count = 0
    for ticket in db.get_overdue_tickets():
        if ticket["status"] == "Escalated":
            continue
        db.update_ticket(ticket["ticket_id"], TicketUpdate(status="Escalated"))
        db.create_notification(NotificationCreate(
            ticket_id=ticket["ticket_id"],
            recipient=ticket["telegram_id"],
            channel="dashboard",
            message=f"Ticket #{ticket['ticket_id']} has been escalated because it passed its target resolution time.",
            status="pending",
        ))
        count += 1
    return count
