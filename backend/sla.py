"""Target-resolution calculation for FlowDesk."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from backend import constants
from backend.llm import call_llm
from backend.llm_schemas import TARGET_RESOLUTION_SCHEMA, TargetResolutionResult


MAX_TARGET_HOURS = 168


def estimate_target_resolution(
    description: str,
    department: dict | None,
    created_at: str | None = None,
) -> TargetResolutionResult:
    dept_name = (department or {}).get("name", "Unassigned")
    prompt = f"""Estimate the target resolution window for this campus complaint.
Use urgency Low, Medium, High, or Critical. Return target_hours between 1 and {MAX_TARGET_HOURS}.
Set a practical target based only on safety, health, blocked access, large group impact,
and operational urgency.

Department: {dept_name}

Complaint:
{description}
"""
    result = TargetResolutionResult.model_validate(call_llm(prompt, TARGET_RESOLUTION_SCHEMA))
    bounded_hours = max(1, min(MAX_TARGET_HOURS, int(result.target_hours or 48)))
    return TargetResolutionResult(
        urgency=result.urgency,
        target_hours=bounded_hours,
        explanation=result.explanation,
    )


def target_timestamp(created_at: str, hours: int) -> str:
    try:
        start = datetime.fromisoformat(created_at)
    except Exception as exc:
        raise ValueError(f"Invalid created_at timestamp format '{created_at}': {exc}") from exc
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    return (start + timedelta(hours=hours)).isoformat()


def calculate_sla_deadline(priority: str, created_at: str) -> str:
    """Compatibility wrapper for old callers."""
    if priority not in constants.SLA_HOURS:
        raise ValueError(f"Invalid priority '{priority}'.")
    return target_timestamp(created_at, constants.SLA_HOURS[priority])
