
"""Main Streamlit entry point for FlowDesk.

Sets up page configuration, sidebar navigation, and routes to the
appropriate page based on user selection.
"""
"""FlowDesk admin dashboard entry point."""

"""FlowDesk admin dashboard entry point.

Sets up the dashboard page and displays the metrics bar, ticket table,
and event timeline.
"""

import streamlit as st

from components.metrics_bar import render_metrics_bar
from components.ticket_table import render_ticket_table
from components.event_timeline import show_event_timeline

st.title("FlowDesk Dashboard")

# fake data for now — replace with real SQLite data later
tickets = [
    {"id": 1, "title": "Wifi down", "status": "Open", "created_at": "10:00"},
    {"id": 2, "title": "Fan broken", "status": "Escalated", "created_at": "11:00"},
    {"id": 3, "title": "Mess food cold", "status": "Resolved", "created_at": "09:00"},
]

render_metrics_bar({"Open": 1, "Escalated": 1, "Resolved": 1})
render_ticket_table(tickets)

show_event_timeline([
    {"action": "CLASSIFIED", "timestamp": "10:00"},
    {"action": "ROUTED", "timestamp": "10:01"},
    {"action": "ESCALATED", "timestamp": "14:00"},
])