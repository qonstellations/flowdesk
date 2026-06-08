"""Reusable ticket table component for FlowDesk.

Renders a list of tickets as an interactive Streamlit table and returns
the selected ticket ID, if any.
"""

"""Reusable ticket table component for FlowDesk.

Renders a list of tickets as a table, newest first.
"""

import streamlit as st


def render_ticket_table(tickets: list) -> None:
    """Render tickets as a table, newest first.

    Args:
        tickets: A list of ticket dictionaries.
    """
    if not tickets:
        st.write("No tickets yet.")
        return

    rows = sorted(tickets, key=lambda t: t["created_at"], reverse=True)
    st.table(rows)
    # temp test — delete later
render_ticket_table([
    {"id": 1, "title": "Wifi down", "status": "Open", "created_at": "10:00"},
    {"id": 2, "title": "Fan broken", "status": "Escalated", "created_at": "11:00"},
])