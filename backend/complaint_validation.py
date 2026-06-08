"""Deterministic validation for incoming ticket text.

This module is intentionally model-independent. The LLM can help with
classification and cleanup after this gate, but it should not be the only
thing deciding whether random text becomes a persisted ticket.
"""

from __future__ import annotations

from dataclasses import dataclass
import re


_FILLER_MESSAGES = {
    "hi",
    "hello",
    "hey",
    "test",
    "testing",
    "asdf",
    "asdfgh",
    "qwerty",
    "ok",
    "okay",
    "lol",
    "lmao",
    "123",
}

_CAMPUS_TERMS = {
    "academic",
    "academics",
    "attendance",
    "bathroom",
    "bed",
    "block",
    "bus",
    "campus",
    "canteen",
    "class",
    "classes",
    "classroom",
    "course",
    "credits",
    "door",
    "electricity",
    "exam",
    "fan",
    "fee",
    "food",
    "grade",
    "grades",
    "geyser",
    "hostel",
    "internet",
    "lab",
    "library",
    "lift",
    "maintenance",
    "mess",
    "network",
    "professor",
    "registration",
    "room",
    "shower",
    "toilet",
    "water",
    "wifi",
    "wi-fi",
    "window",
}

_ISSUE_TERMS = {
    "bad",
    "blocked",
    "broken",
    "burst",
    "clogged",
    "complaint",
    "damaged",
    "delay",
    "dirty",
    "down",
    "failed",
    "failure",
    "issue",
    "leak",
    "leakage",
    "leaking",
    "low",
    "missing",
    "not",
    "poor",
    "problem",
    "reported",
    "sick",
    "smell",
    "unsafe",
    "unhygienic",
    "urgent",
    "working",
}


@dataclass(frozen=True)
class ComplaintValidation:
    """Result of validating a user's requested ticket text."""

    is_valid: bool
    rejection_reason: str = ""


def validate_complaint_text(text: str) -> ComplaintValidation:
    """Return whether *text* looks like a real campus issue.

    The gate rejects obvious garbage, chat, and spam while still allowing
    vague complaint-like messages such as "campus issue in hostel" or
    "another problem reported".
    """
    normalized = _normalize(text)
    if not normalized:
        return ComplaintValidation(False, "Please describe the campus issue you want help with.")

    if normalized in _FILLER_MESSAGES:
        return ComplaintValidation(False, "That looks like a test or chat message, not a support issue.")

    words = _words(normalized)
    if len(words) < 2:
        return ComplaintValidation(False, "Please include a few words describing the issue.")

    if len(normalized) < 10 and not _contains_known_signal(words):
        return ComplaintValidation(False, "Please add a little more detail about the issue.")

    if _looks_like_repeated_noise(words):
        return ComplaintValidation(False, "That message looks like repeated random text, not a campus issue.")

    if not _contains_known_signal(words):
        return ComplaintValidation(
            False,
            "Please describe a real campus facility, service, hostel, mess, or academic issue.",
        )

    return ComplaintValidation(True)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z][a-z-]*", text)


def _contains_known_signal(words: list[str]) -> bool:
    word_set = set(words)
    return bool(word_set & _CAMPUS_TERMS) or bool(word_set & _ISSUE_TERMS)


def _looks_like_repeated_noise(words: list[str]) -> bool:
    if len(words) < 4:
        return False

    unique_ratio = len(set(words)) / len(words)
    average_word_length = sum(len(word) for word in words) / len(words)
    has_signal = _contains_known_signal(words)

    return unique_ratio <= 0.5 and average_word_length <= 8 and not has_signal
