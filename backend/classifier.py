"""LLM-based complaint classification for FlowDesk.

Analyses the free-text complaint description and returns a structured
``{"category": ..., "priority": ...}`` dict whose values are guaranteed
to be valid per ``constants.CATEGORIES`` and ``constants.PRIORITIES``.
"""

from __future__ import annotations

from backend import constants


def classify_complaint(description: str) -> dict:
    """Classify a complaint description into a category and priority.

    Parameters
    ----------
    description:
        The raw, user-supplied complaint text.

    Returns
    -------
    dict
        ``{"category": <str>, "priority": <str>}`` where both values
        are drawn from the canonical allowed sets in ``constants``.
    """
    raise NotImplementedError("Not yet implemented")


def _validate_category(category: str) -> str:
    """Sanitise a predicted category string.

    If *category* is not in ``constants.CATEGORIES``, falls back to
    ``"Other"``.
    """
    raise NotImplementedError("Not yet implemented")


def _validate_priority(priority: str) -> str:
    """Sanitise a predicted priority string.

    If *priority* is not in ``constants.PRIORITIES``, falls back to
    ``"Medium"``.
    """
    raise NotImplementedError("Not yet implemented")
