"""SLA deadline calculation for FlowDesk.

Computes the expected resolution deadline by adding the SLA window
(from ``constants.SLA_HOURS``) to the ticket's creation timestamp.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from backend import constants


def calculate_sla_deadline(priority: str, created_at: str) -> str:
    """Compute the SLA deadline as an ISO-8601 datetime string.

    Parameters
    ----------
    priority:
        One of the values in ``constants.PRIORITIES``.
    created_at:
        ISO-8601 formatted datetime string representing when the ticket
        was created (e.g. ``"2026-06-07T12:00:00"``).

    Returns
    -------
    str
        ISO-8601 datetime string for the SLA deadline.

    Raises
    ------
    ValueError
        If *priority* is not recognised.
    """
    raise NotImplementedError("Not yet implemented")
