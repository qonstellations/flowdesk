"""Ticket processing workflow for verified, complete complaints."""

from __future__ import annotations

from backend import db, router, sla
from backend.llm import call_llm
from backend.llm_schemas import INTAKE_SCHEMA, IntakeResult
from backend.models import EventCreate, GraphState, NotificationCreate, TicketCreate
from backend.telegram_helpers import format_ticket_reply


def run_workflow(raw_message: str, telegram_id: str) -> GraphState:
    """Create a ticket from a verified and complete Telegram complaint."""
    if not telegram_id:
        raise ValueError("telegram_id is required to create a ticket.")

    user = db.get_user_by_telegram_id(telegram_id)
    if not user or not user.get("is_verified"):
        raise PermissionError("Telegram user must be linked to a verified Google account before creating tickets.")

    intake = _extract_intake(raw_message)
    routing = router.route_ticket(intake.description, intake.title)
    department = db.get_department(routing.department_id)
    created_at = db.utc_now()
    target = sla.estimate_target_resolution(intake.description, department, created_at)
    target_at = sla.target_timestamp(created_at, target.target_hours)

    ticket_id = db.create_ticket(TicketCreate(
        telegram_id=telegram_id,
        title=intake.title,
        description=intake.description,
        raw_message=raw_message,
        category=routing.department_name,
        location=intake.location or "Unknown",
        priority=target.urgency,
        department_id=routing.department_id,
        routing_reason=routing.reason,
        routing_confidence=routing.confidence,
        target_resolution_at=target_at,
    ))

    db.create_event(EventCreate(
        ticket_id=ticket_id,
        actor_type="system",
        actor_name="agent",
        action="ROUTED",
        details=f"Assigned to {routing.department_name}. Reason: {routing.reason}",
    ))
    db.create_event(EventCreate(
        ticket_id=ticket_id,
        actor_type="system",
        actor_name="agent",
        action="TARGET_RESOLUTION_SET",
        details=f"{target.urgency} urgency, {target.target_hours} hour target. {target.explanation}",
    ))

    reply = format_ticket_reply(
        ticket_id=ticket_id,
        department=routing.department_name,
        priority=target.urgency,
        target_resolution_at=target_at,
    )
    db.create_notification(NotificationCreate(
        ticket_id=ticket_id,
        recipient=telegram_id,
        channel="telegram",
        message=reply,
        status="pending",
    ))

    return GraphState(
        raw_message=raw_message,
        telegram_id=telegram_id,
        student_id=user.get("verified_email") or user.get("name"),
        ticket_id=ticket_id,
        title=intake.title,
        description=intake.description,
        category=routing.department_name,
        location=intake.location,
        priority=target.urgency,
        assigned_dept=routing.department_name,
        department_id=routing.department_id,
        routing_reason=routing.reason,
        routing_confidence=routing.confidence,
        target_resolution_at=target_at,
        sla_deadline=target_at,
        status="Open",
        created_at=created_at,
        agent_notes=[
            "Complaint normalized by Intake Agent.",
            f"Ticket routed to {routing.department_name}.",
            f"Target resolution set to {target_at}.",
            f"Ticket saved with ID {ticket_id}.",
        ],
    )


def _extract_intake(raw_message: str) -> IntakeResult:
    prompt = f"""Extract and normalize a complete university campus complaint.
Return a concise title, clear description, and location. Use "Unknown" only if no location
is required or no location is present.

Complaint:
{raw_message}
"""
    result = IntakeResult.model_validate(call_llm(prompt, INTAKE_SCHEMA))
    return IntakeResult(
        title=result.title.strip() or "Campus Issue Report",
        description=result.description.strip() or raw_message,
        location=result.location.strip() or "Unknown",
    )
