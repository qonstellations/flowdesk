
"""Main Streamlit entry point for FlowDesk.

Sets up page configuration, sidebar navigation, and routes to the
appropriate page based on user selection.
"""
"""FlowDesk admin dashboard entry point."""

import streamlit as st

from components.metrics_bar import render_metrics_bar
from components.event_timeline import show_event_timeline

st.set_page_config(page_title="FlowDesk", page_icon="*", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&display=swap');
.stApp {
    background: linear-gradient(rgba(10,14,26,0.94), rgba(10,14,26,0.97)),
        url('https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=1600') center/cover fixed;
}
html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; color: #E8ECF5; }
.hero { text-align: center; padding: 30px 20px 20px; }
.hero h1 { font-size: 2.8rem; font-weight: 700; margin: 0;
    background: linear-gradient(90deg,#00E5FF,#7C4DFF);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.hero p { color: #9AA4C0; font-size: 1.1rem; margin-top: 6px; }
.flow { display:flex; justify-content:center; align-items:center; flex-wrap:wrap; gap:8px; margin:20px 0 30px; }
.flow-step { background: linear-gradient(145deg,#141A2E,#0E1424); border:1px solid rgba(0,229,255,0.3);
    border-radius:12px; padding:12px 18px; font-size:0.85rem; box-shadow:0 0 14px rgba(0,229,255,0.1); }
.flow-arrow { color:#00E5FF; font-size:1.3rem; }
.metric-card { background: linear-gradient(145deg,#141A2E,#0E1424); border:1px solid rgba(0,229,255,0.25);
    border-radius:14px; padding:22px 18px; text-align:center; box-shadow:0 0 18px rgba(0,229,255,0.12);
    transition: all 0.2s ease; }
.metric-card:hover { transform: translateY(-3px); box-shadow:0 0 26px rgba(0,229,255,0.3); }
.metric-value { font-size:2.4rem; font-weight:700; color:#00E5FF; text-shadow:0 0 12px rgba(0,229,255,0.5); }
.metric-label { font-size:0.85rem; letter-spacing:0.12em; text-transform:uppercase; color:#8A94B0; margin-top:4px; }
.ticket { background: rgba(20,26,46,0.7); border-radius:10px; padding:14px 18px; margin-bottom:10px;
    border-left:4px solid #00E5FF; display:flex; justify-content:space-between; align-items:center; }
.ticket.overdue { border-left-color:#FF4D6D; box-shadow:0 0 14px rgba(255,77,109,0.15); }
.badge { padding:3px 12px; border-radius:20px; font-size:0.75rem; font-weight:600; }
.b-open { background:rgba(0,229,255,0.15); color:#00E5FF; }
.b-escalated { background:rgba(255,77,109,0.15); color:#FF4D6D; }
.b-resolved { background:rgba(76,217,123,0.15); color:#4CD97B; }
section[data-testid="stSidebar"] { background: rgba(14,20,36,0.9); border-right:1px solid rgba(0,229,255,0.15); }
</style>
""", unsafe_allow_html=True)

# ---- Ticket data lives in session_state so buttons can change it ----
def default_tickets():
    return [
        {"id": 1, "title": "Wifi down in B-block", "status": "Open", "dept": "IT Department", "created_at": "10:00", "overdue": False},
        {"id": 2, "title": "Fan broken in room 204", "status": "Open", "dept": "Hostel Maintenance Team", "created_at": "08:00", "overdue": True},
        {"id": 3, "title": "Mess food served cold", "status": "Resolved", "dept": "Mess Committee", "created_at": "09:00", "overdue": False},
    ]

if "tickets" not in st.session_state:
    st.session_state.tickets = default_tickets()

# ---- Sidebar navigation ----
with st.sidebar:
    st.markdown("### FlowDesk")
    page = st.radio("Navigation", ["Dashboard", "Tickets", "Analytics", "Settings"])
    st.markdown("---")
    st.markdown("Status: **Online**")

# ---- Hero ----
st.markdown("""
<div class="hero"><h1>&#9889; FlowDesk</h1>
<p>An AI portal to resolve your campus issues — faster.</p></div>
""", unsafe_allow_html=True)

tickets = st.session_state.tickets

def render_tickets(ticket_list):
    if not ticket_list:
        st.write("No tickets yet.")
        return
    rows = sorted(ticket_list, key=lambda t: t["created_at"], reverse=True)
    for t in rows:
        cls = "ticket overdue" if t["overdue"] and t["status"] != "Resolved" else "ticket"
        badge = {"Open": "b-open", "Escalated": "b-escalated", "Resolved": "b-resolved"}.get(t["status"], "b-open")
        st.markdown(f"""
        <div class="{cls}">
            <div><b>#{t['id']} {t['title']}</b><br>
            <span style="color:#8A94B0; font-size:0.8rem;">{t['dept']} · {t['created_at']}</span></div>
            <span class="badge {badge}">{t['status']}</span>
        </div>""", unsafe_allow_html=True)

# ---- Pages ----
if page == "Dashboard":
    st.markdown("""
    <div class="flow">
        <div class="flow-step">Complaint</div><div class="flow-arrow">&#8594;</div>
        <div class="flow-step">AI Intake</div><div class="flow-arrow">&#8594;</div>
        <div class="flow-step">Classify</div><div class="flow-arrow">&#8594;</div>
        <div class="flow-step">Route</div><div class="flow-arrow">&#8594;</div>
        <div class="flow-step">SLA Deadline</div><div class="flow-arrow">&#8594;</div>
        <div class="flow-step">Resolved</div>
    </div>""", unsafe_allow_html=True)

    # metrics computed live from current tickets
    counts = {
        "Open": len([t for t in tickets if t["status"] == "Open"]),
        "Overdue": len([t for t in tickets if t["overdue"] and t["status"] != "Resolved"]),
        "Escalated": len([t for t in tickets if t["status"] == "Escalated"]),
        "Resolved": len([t for t in tickets if t["status"] == "Resolved"]),
    }
    render_metrics_bar(counts)

    st.markdown("###")
    col1, col2 = st.columns(2)
    if col1.button("⚡ Trigger SLA Engine"):
        for t in st.session_state.tickets:
            if t["overdue"] and t["status"] == "Open":
                t["status"] = "Escalated"
        st.rerun()
    if col2.button("📥 Load Demo Data"):
        st.session_state.tickets = default_tickets()
        st.rerun()

    st.markdown("###")
    show_event_timeline([
        {"action": "CLASSIFIED", "timestamp": "10:00"},
        {"action": "ROUTED", "timestamp": "10:01"},
        {"action": "ESCALATED", "timestamp": "14:00"},
    ])

elif page == "Tickets":
    st.subheader("All Tickets")
    render_tickets(tickets)
    st.markdown("---")
    st.markdown("**Manual escalate**")
    open_ids = [t["id"] for t in tickets if t["status"] == "Open"]
    if open_ids:
        chosen = st.selectbox("Pick a ticket to escalate", open_ids)
        if st.button("Escalate this ticket"):
            for t in st.session_state.tickets:
                if t["id"] == chosen:
                    t["status"] = "Escalated"
            st.rerun()
    else:
        st.write("No open tickets to escalate.")

elif page == "Analytics":
    st.subheader("Analytics")
    counts = {
        "Open": len([t for t in tickets if t["status"] == "Open"]),
        "Escalated": len([t for t in tickets if t["status"] == "Escalated"]),
        "Resolved": len([t for t in tickets if t["status"] == "Resolved"]),
    }
    st.bar_chart(counts)

elif page == "Settings":
    st.subheader("Settings")
    st.write("Preferences and configuration — coming soon.")