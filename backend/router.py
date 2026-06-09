"""Department-backed ticket routing."""

from __future__ import annotations

from backend import db
from backend.llm import call_llm
from backend.llm_schemas import ROUTING_SCHEMA, RoutingResult


def route_ticket(description: str, title: str = "") -> RoutingResult:
    """Route a complaint to one active admin-created department."""
    departments = db.get_active_departments()
    if not departments:
        raise RuntimeError("No active departments are configured. An admin must add departments before routing tickets.")

    prompt_departments = "\n".join(
        (
            f"- ID {dept['department_id']}: {dept['name']}\n"
            f"  Responsibilities: {dept.get('responsibilities') or 'Not provided'}"
        )
        for dept in departments
    )
    prompt = f"""Route this campus complaint to exactly one active department.
Choose only from the department IDs listed below.

Departments:
{prompt_departments}

Ticket title:
{title}

Complaint:
{description}
"""
    result = RoutingResult.model_validate(call_llm(prompt, ROUTING_SCHEMA))
    allowed_by_id = {int(dept["department_id"]): dept for dept in departments}
    selected = allowed_by_id.get(result.department_id)
    if selected:
        return RoutingResult(
            department_id=int(selected["department_id"]),
            department_name=selected["name"],
            confidence=result.confidence,
            reason=result.reason,
        )

    general = next((dept for dept in departments if dept["name"].strip().lower() == "general admin"), None)
    if general:
        return RoutingResult(
            department_id=int(general["department_id"]),
            department_name=general["name"],
            confidence=0.25,
            reason="LLM selected an unknown department; routed to active General Admin fallback.",
        )

    raise ValueError("LLM selected a department that is not active and no General Admin fallback exists.")
