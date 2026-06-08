
"""Main Streamlit entry point for FlowDesk.

Sets up page configuration, sidebar navigation, and routes to the
appropriate page based on user selection.
"""
"""FlowDesk admin dashboard entry point."""

"""FlowDesk admin dashboard entry point."""

import streamlit as st

from components.metrics_bar import render_metrics_bar
from components.ticket_table import render_ticket_table
from components.event_timeline import show_event_timeline

st.set_page_config(page_title="FlowDesk", page_icon="*", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&display=swap');

.stApp {
    background: radial-gradient(circle at 20% 0%, #16204A 0%, #0A0E1A 45%),
                radial-gradient(circle at 90% 100%, #1A0E3A 0%, transparent 50%);
    background-attachment: fixed;
}
html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
    color: #E8ECF5;
}

/* Hero */
.hero {
    text-align: center;
    padding: 40px 20px 30px 20px;
}
.hero h1 {
    font-size: 3rem;
    font-weight: 700;
    margin: 0;
    background: linear-gradient(90deg, #00E5FF, #7C4DFF);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.hero p {
    color: #9AA4C0;
    font-size: 1.15rem;
    margin-top: 8px;
    letter-spacing: 0.02em;
}

/* Flow chart */
.flow {
    display: flex;
    justify-content: center;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
    margin: 25px 0 40px 0;
}
.flow-step {
    background: linear-gradient(145deg, #141A2E, #0E1424);
    border: 1px solid rgba(0, 229, 255, 0.3);
    border-radius: 12px;
    padding: 14px 20px;
    font-size: 0.9rem;
    color: #E8ECF5;
    box-shadow: 0 0 14px rgba(0, 229, 255, 0.1);
}
.flow-arrow {
    color: #00E5FF;
    font-size: 1.4rem;
}

/* Metric cards */
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
.metric-value { font-size: 2.4rem; font-weight: 700; color: #00E5FF; text-shadow: 0 0 12px rgba(0, 229, 255, 0.5); }
.metric-label { font-size: 0.85rem; letter-spacing: 0.12em; text-transform: uppercase; color: #8A94B0; margin-top: 4px; }

section[data-testid="stSidebar"] { background: #0E1424; border-right: 1px solid rgba(0,229,255,0.15); }
</style>
""", unsafe_allow_html=True)

# ---- Sidebar ----
with st.sidebar:
    st.markdown("### &#9889; FlowDesk", unsafe_allow_html=True)
    st.markdown("**Navigation**")
    st.markdown("- Dashboard\n- Tickets\n- Analytics\n- Settings")
    st.markdown("---")
    st.markdown("Status: **Online**")

# ---- Hero entry section ----
st.markdown("""
<div class="hero">
    <h1>&#9889; FlowDesk</h1>
    <p>An AI portal to resolve your campus issues — faster.</p>
</div>
""", unsafe_allow_html=True)

# ---- How it works flow chart ----
st.markdown("""
<div class="flow">
    <div class="flow-step">Complaint</div>
    <div class="flow-arrow">&#8594;</div>
    <div class="flow-step">AI Intake</div>
    <div class="flow-arrow">&#8594;</div>
    <div class="flow-step">Classify</div>
    <div class="flow-arrow">&#8594;</div>
    <div class="flow-step">Route to Dept</div>
    <div class="flow-arrow">&#8594;</div>
    <div class="flow-step">SLA Deadline</div>
    <div class="flow-arrow">&#8594;</div>
    <div class="flow-step">Resolved</div>
</div>
""", unsafe_allow_html=True)

# ---- Live data ----
tickets = [
    {"id": 1, "title": "Wifi down", "status": "Open", "created_at": "10:00"},
    {"id": 2, "title": "Fan broken", "status": "Escalated", "created_at": "11:00"},
    {"id": 3, "title": "Mess food cold", "status": "Resolved", "created_at": "09:00"},
]

render_metrics_bar({"Open": 1, "Escalated": 1, "Resolved": 1})
st.markdown("###")  # spacing
render_ticket_table(tickets)
show_event_timeline([
    {"action": "CLASSIFIED", "timestamp": "10:00"},
    {"action": "ROUTED", "timestamp": "10:01"},
    {"action": "ESCALATED", "timestamp": "14:00"},
])