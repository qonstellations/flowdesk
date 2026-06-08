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