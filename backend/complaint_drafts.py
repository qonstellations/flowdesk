"""Telegram complaint clarification state."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import ValidationError

from backend import db
from backend.complaint_validation import validate_complaint_text
from backend.llm import call_llm
from backend.llm_schemas import (
    CLARIFICATION_SCHEMA,
    COMPLAINT_VALIDATION_SCHEMA,
    ClarificationResult,
    ComplaintValidationResult,
)


@dataclass(frozen=True)
class ComplaintReadiness:
    is_valid: bool
    is_complete: bool
    complaint_text: str
    missing_fields: list[str]
    questions: list[str]
    reason: str = ""


def inspect_complaint(text: str) -> ComplaintReadiness:
    deterministic = validate_complaint_text(text)
    if not deterministic.is_valid:
        return ComplaintReadiness(False, False, text, [], [], deterministic.rejection_reason)

    validation_prompt = f"""You validate complaints for a university campus helpdesk.
Decide if the message is a real campus issue and if staff have enough detail to act.

Required signals:
- a real campus service/facility/academic issue
- affected service or facility
- location when location is needed for action
- urgency/severity when the issue sounds risky or blocking
- enough context for staff to understand the next action

Return missing_fields using short backend names such as issue, service, location, urgency, context.

Student message:
{text}
"""
    raw_validation = call_llm(validation_prompt, COMPLAINT_VALIDATION_SCHEMA)
    validation = ComplaintValidationResult.model_validate(raw_validation)

    if not validation.is_valid:
        return ComplaintReadiness(False, False, text, validation.missing_fields, [], validation.reason)

    clarification_prompt = f"""Normalize this campus complaint and ask at most two focused follow-up questions
only if fields are missing. Do not ask generic questions.

Complaint:
{text}

Missing fields already detected:
{', '.join(validation.missing_fields) or 'none'}
"""
    raw_clarification = call_llm(clarification_prompt, CLARIFICATION_SCHEMA)
    clarification = ClarificationResult.model_validate(raw_clarification)

    missing = clarification.missing_fields or validation.missing_fields
    questions = clarification.next_questions[:2]
    complete = validation.is_complete and not missing
    return ComplaintReadiness(
        is_valid=True,
        is_complete=complete,
        complaint_text=clarification.normalized_complaint or text,
        missing_fields=missing,
        questions=questions,
        reason=validation.reason,
    )


def save_draft(
    telegram_id: str,
    chat_id: str,
    complaint_text: str,
    missing_fields: list[str],
    questions: list[str],
    answers: list[str] | None = None,
) -> None:
    db.upsert_complaint_draft(
        telegram_id=telegram_id,
        chat_id=chat_id,
        draft_complaint=complaint_text,
        missing_fields=missing_fields,
        asked_questions=questions,
        answers=answers or [],
    )


def merge_draft_answer(telegram_id: str, answer: str) -> tuple[dict, str] | None:
    draft = db.get_active_complaint_draft(telegram_id)
    if not draft:
        return None
    answers = list(draft.get("answers") or [])
    answers.append(answer)
    combined = (
        f"{draft['draft_complaint']}\n\n"
        f"Additional student answer: {answer}"
    )
    draft["answers"] = answers
    return draft, combined


def clear_draft(telegram_id: str) -> None:
    db.delete_complaint_draft(telegram_id)


def readiness_error_message(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        return "The AI response did not match the required complaint schema."
    return str(exc)
