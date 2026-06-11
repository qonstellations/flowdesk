"""Telegram complaint clarification state."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import ValidationError

from backend import db
from backend.complaint_validation import validate_complaint_text
from backend.llm import call_llm
from backend.llm_schemas import (
    CLARIFICATION_SCHEMA,
    COMPLAINT_INSPECTION_SCHEMA,
    COMPLAINT_VALIDATION_SCHEMA,
    ClarificationResult,
    ComplaintInspectionResult,
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

    inspection_prompt = f"""You validate, normalize, and clarify campus complaints for a university campus helpdesk.

Review the student's message:
"{text}"

Identify the following details from the message:
- Service/facility (e.g., Wi-Fi, heating, printer, dining)
- Location (e.g., dorm room 405, library floor 2)
- Urgency/severity (e.g., water leak is High/Critical, slow Wi-Fi is Low/Medium)
- Context/Description of the issue (e.g., not working since yesterday)

Determine if the message is:
1. A real campus issue (set `is_valid` to true/false).
2. Complete enough for staff to act (set `is_complete` to true if service, location, urgency, and context are all clear or inferred. Set to false if any critical information is missing).

If any of the fields (issue, service, location, urgency, context) are missing and needed:
- List them in `missing_fields` (using only these lowercase names: 'issue', 'service', 'location', 'urgency', 'context').
- Generate exactly 1 or 2 focused, direct follow-up questions in `next_questions` to ask the student for that missing information. Do not ask generic questions.

Normalize the student's complaint into a clear, professional summary for helpdesk staff in `normalized_complaint`.
"""
    raw_inspection = call_llm(inspection_prompt, COMPLAINT_INSPECTION_SCHEMA)
    inspection = ComplaintInspectionResult.model_validate(raw_inspection)

    if not inspection.is_valid:
        return ComplaintReadiness(False, False, text, inspection.missing_fields, [], inspection.reason)

    missing = inspection.missing_fields
    questions = inspection.next_questions[:2]
    complete = inspection.is_complete and not missing
    return ComplaintReadiness(
        is_valid=True,
        is_complete=complete,
        complaint_text=inspection.normalized_complaint or text,
        missing_fields=missing,
        questions=questions,
        reason=inspection.reason,
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
