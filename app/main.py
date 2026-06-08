
"""Main Streamlit entry point for FlowDesk.

Sets up page configuration, sidebar navigation, and routes to the
appropriate page based on user selection.
"""
"""FlowDesk admin dashboard entry point."""

"""FlowDesk admin dashboard entry point.

Sets up the dashboard page and displays the metrics bar, ticket table,
and event timeline.
"""

"""FlowDesk admin dashboard entry point."""

import streamlit as st

from components.metrics_bar import render_metrics_bar
from components.ticket_table import render_ticket_table
from components.event_timeline import show_event_timeline

st.set_page_config(page_title="FlowDesk", page_icon="⚡", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&display=swap');

.stApp {
    background: #0A0E1A;
}
html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
    color: #E8ECF5;
}
.metric-card {
    background: linear-gradient(145deg, #141A2E, #0E1424);
    border: 1px solid rgba(0, 229, 255, 0.25);
    border-radius: 14px;
    padding: 22px 18px;
    text-align: center;
    box-shadow: 0 0 18px rgba(0, 229, 255, 0.12);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.metric-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 0 26px rgba(0, 229, 255, 0.3);
}
.metric-value {
    font-size: 2.4rem;
    font-weight: 700;
    color: #00E5FF;
    text-shadow: 0 0 12px rgba(0, 229, 255, 0.5);
}
.metric-label {
    font-size: 0.85rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #8A94B0;
    margin-top: 4px;
}
</style>
""", unsafe_allow_html=True)

st.title("⚡ FlowDesk Dashboard")

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