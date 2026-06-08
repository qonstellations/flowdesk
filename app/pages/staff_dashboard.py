from datetime import datetime, timezone

import streamlit as st

import backend.db as db
from backend.models import TicketUpdate
from components.event_timeline import show_event_timeline
from components.metrics_bar import render_metrics_bar
from components.ticket_table import render_ticket_table

_DEPARTMENTS = [
    "IT Department",
    "Hostel Maintenance Team",
    "Campus Facilities Team",
    "Mess Committee",
    "Academic Office",
    "General Admin",
]

_ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    "Open":       ["In Progress"],
    "Assigned":   ["In Progress"],
    "In Progress":["Resolved"],
    "Resolved":   ["Closed", "Reopened"],
    "Reopened":   ["In Progress"],
    "Escalated":  ["In Progress", "Resolved"],
    "Closed":     [],
}


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

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Status", ticket["status"])
    col2.metric("Priority", ticket["priority"])
    col3.metric("Category", ticket["category"])
    sla = ticket.get("sla_deadline", "")
    if sla:
        try:
            dl = datetime.fromisoformat(sla)
            if dl.tzinfo is None:
                dl = dl.replace(tzinfo=timezone.utc)
            overdue = datetime.now(timezone.utc) > dl and ticket["status"] not in ("Resolved", "Closed")
            col4.metric("SLA", "⚠ OVERDUE" if overdue else sla[:10])
        except Exception:
            col4.metric("SLA", sla[:10])
    else:
        col4.metric("SLA", "—")

    with st.expander("📄 Description"):
        st.write(ticket["description"])
        if ticket.get("location"):
            st.caption(f"📍 {ticket['location']}")

    transitions = _ALLOWED_TRANSITIONS.get(ticket["status"], [])
    if transitions:
        col_s, col_b = st.columns([2, 1])
        new_status = col_s.selectbox("Move to", transitions, key=f"staff_ns_{ticket_id}")
        col_b.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
        if col_b.button("✓ Update", key=f"staff_upd_{ticket_id}", use_container_width=True, type="primary"):
            update = TicketUpdate(status=new_status)
            if new_status == "Resolved":
                update = TicketUpdate(status=new_status, resolved_at=datetime.now(timezone.utc).isoformat())
            elif new_status == "Closed":
                update = TicketUpdate(status=new_status, closed_at=datetime.now(timezone.utc).isoformat())
            db.update_ticket(ticket_id, update)
            st.success(f"Ticket #{ticket_id} moved to **{new_status}**.")
            st.rerun()
    else:
        st.info("No further transitions available for this ticket.")

    st.markdown("---")
    events = db.get_events_by_ticket(ticket_id)
    show_event_timeline(events)
