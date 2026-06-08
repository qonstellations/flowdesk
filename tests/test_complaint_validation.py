"""Tests for deterministic ticket text validation."""

from backend.complaint_validation import validate_complaint_text


def test_rejects_repeated_garbage_text() -> None:
    result = validate_complaint_text("boogie boogie pookie pookie")

    assert result.is_valid is False
    assert result.rejection_reason


def test_rejects_casual_chat() -> None:
    result = validate_complaint_text("hello")

    assert result.is_valid is False


def test_accepts_clear_campus_issue() -> None:
    result = validate_complaint_text("Wi-Fi is not working in Hostel Block A")

    assert result.is_valid is True


def test_accepts_vague_issue_like_complaint() -> None:
    result = validate_complaint_text("Another campus problem reported")

    assert result.is_valid is True
