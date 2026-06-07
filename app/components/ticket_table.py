"""Reusable ticket table component for FlowDesk.

Renders a list of tickets as an interactive Streamlit table and returns
the selected ticket ID, if any.
"""

import pandas as pd
import streamlit as st


def render_ticket_table(tickets: list[dict]) -> int | None:
    """Render a ticket table and return the selected ticket ID.

    Args:
        tickets: A list of ticket dictionaries to display.

    Returns:
        The ``ticket_id`` of the selected row, or ``None`` if no
        selection was made.
    """
    pass
