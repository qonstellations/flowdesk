"""Ticket routing logic for FlowDesk.

Maps a complaint category to the responsible department using the
``DEPARTMENT_ROUTING`` lookup in ``constants``.
"""

from __future__ import annotations

from backend import constants


def route_ticket(category: str) -> str:
    """Return the department name responsible for *category*.

    Falls back to ``"General Admin"`` when the category is not found in
    ``constants.DEPARTMENT_ROUTING``.

    Parameters
    ----------
    category:
        One of the values in ``constants.CATEGORIES``.

    Returns
    -------
    str
        The department name that should handle this ticket.
    """
    if not category:
        return "General Admin"
        
    cleaned = category.strip()
    return constants.DEPARTMENT_ROUTING.get(cleaned, "General Admin")

