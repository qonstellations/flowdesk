import streamlit as st

import backend.db as db
from components.metrics_bar import render_metrics_bar
from components.ticket_detail import render_ticket_detail
from components.ticket_table import render_ticket_table

_DEPARTMENTS = [
    "IT Department",
    "Hostel Maintenance Team",
    "Campus Facilities Team",
    "Mess Committee",
    "Academic Office",
    "General Admin",
]


def render() -> None:
    st.markdown('<div class="fd-section">Staff Dashboard</div>', unsafe_allow_html=True)

    col_dept, col_refresh = st.columns([3, 1])
    with col_dept:
        dept = st.selectbox(
            "Your Department",
            _DEPARTMENTS,
            key="staff_dept",
        )
    with col_refresh:
        st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    tickets = db.get_tickets_by_department(dept)

    open_count      = sum(1 for t in tickets if t["status"] in ("Open","Assigned","In Progress","Escalated","Reopened"))
    escalated_count = sum(1 for t in tickets if t["status"] == "Escalated")
    resolved_count  = sum(1 for t in tickets if t["status"] == "Resolved")

    st.markdown("<div style='margin:18px 0 6px;'></div>", unsafe_allow_html=True)
    render_metrics_bar({
        "Total": len(tickets),
        "Active": open_count,
        "Escalated": escalated_count,
        "Resolved": resolved_count,
    })

    st.markdown("---")
    st.markdown(f'<div class="fd-section">Tickets — {dept}</div>', unsafe_allow_html=True)

    if not tickets:
        st.info("No tickets assigned to this department yet.")
        return

    render_ticket_table(tickets)

    st.markdown("---")
    st.markdown('<div class="fd-section">Ticket Actions</div>', unsafe_allow_html=True)

    ticket_options = {f"#{t['ticket_id']} — {t['title']} ({t['status']})": t["ticket_id"] for t in tickets}
    chosen_label = st.selectbox("Select a ticket to act on", list(ticket_options.keys()), key="staff_select")
    chosen_id = ticket_options[chosen_label]

    if chosen_id:
        _show_ticket_actions(chosen_id)


def _show_ticket_actions(ticket_id: int) -> None:
    ticket = db.get_ticket(ticket_id)
    if not ticket:
        st.error(f"Ticket #{ticket_id} not found.")
        return
    events = db.get_events_by_ticket(ticket_id)
    render_ticket_detail(ticket, events, role="staff")
