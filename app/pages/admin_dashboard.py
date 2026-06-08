from datetime import datetime, timezone

import streamlit as st

import backend.db as db
from backend.models import NotificationCreate, TicketUpdate
from components.event_timeline import show_event_timeline
from components.metrics_bar import render_metrics_bar
from components.ticket_table import render_ticket_table


def render() -> None:
    st.markdown('<div class="fd-section">Admin Dashboard</div>', unsafe_allow_html=True)

    tickets = db.get_all_tickets()

    _show_metrics(tickets)
    st.markdown("---")

    col_sla, col_refresh, col_space = st.columns([2, 1, 3])
    with col_sla:
        if st.button("⚡ Trigger SLA Engine", use_container_width=True, type="primary"):
            count = _run_escalation_check()
            if count:
                st.success(f"Escalated {count} overdue ticket(s).")
                st.rerun()
            else:
                st.info("No overdue tickets to escalate.")

    with col_refresh:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    st.markdown("---")

    tab_tickets, tab_analytics = st.tabs(["📋  All Tickets", "📊  Analytics"])

    with tab_tickets:
        _show_all_tickets(tickets)

    with tab_analytics:
        _show_analytics_charts(tickets)


def _show_metrics(tickets: list) -> None:
    total = len(tickets)
    counts = {s: 0 for s in ("Open", "Assigned", "In Progress", "Escalated", "Resolved", "Closed")}
    overdue = 0
    now = datetime.now(timezone.utc)
    for t in tickets:
        counts[t["status"]] = counts.get(t["status"], 0) + 1
        if t.get("sla_deadline") and t["status"] not in ("Resolved", "Closed"):
            try:
                dl = datetime.fromisoformat(t["sla_deadline"])
                if dl.tzinfo is None:
                    dl = dl.replace(tzinfo=timezone.utc)
                if now > dl:
                    overdue += 1
            except Exception:
                pass

    render_metrics_bar({
        "Total": total,
        "Open": counts["Open"],
        "Escalated": counts["Escalated"],
        "Resolved": counts["Resolved"],
        "Overdue": overdue,
    })


def _show_all_tickets(tickets: list) -> None:
    st.markdown('<div class="fd-section">Tickets</div>', unsafe_allow_html=True)

    col_s, col_c, col_p = st.columns(3)
    status_filter = col_s.selectbox(
        "Filter by status",
        ["All", "Open", "Assigned", "In Progress", "Escalated", "Resolved", "Reopened", "Closed"],
        key="admin_status_filter",
    )
    category_filter = col_c.selectbox(
        "Filter by category",
        ["All", "IT & Wi-Fi", "Hostel Maintenance", "Campus Maintenance", "Mess & Food", "Academics", "Other"],
        key="admin_cat_filter",
    )
    priority_filter = col_p.selectbox(
        "Filter by priority",
        ["All", "Critical", "High", "Medium", "Low"],
        key="admin_pri_filter",
    )

    filtered = tickets
    if status_filter != "All":
        filtered = [t for t in filtered if t["status"] == status_filter]
    if category_filter != "All":
        filtered = [t for t in filtered if t["category"] == category_filter]
    if priority_filter != "All":
        filtered = [t for t in filtered if t["priority"] == priority_filter]

    st.caption(f"Showing {len(filtered)} of {len(tickets)} tickets")
    render_ticket_table(filtered)

    if filtered:
        st.markdown('<div class="fd-section">Ticket Detail</div>', unsafe_allow_html=True)
        ticket_ids = [t["ticket_id"] for t in filtered]
        chosen_id = st.selectbox("Select ticket to inspect", ticket_ids, key="admin_detail_select")
        if chosen_id:
            _show_ticket_detail(chosen_id)


def _show_analytics_charts(tickets: list) -> None:
    if not tickets:
        st.info("No ticket data to visualise yet.")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="fd-section">By Status</div>', unsafe_allow_html=True)
        status_counts: dict[str, int] = {}
        for t in tickets:
            status_counts[t["status"]] = status_counts.get(t["status"], 0) + 1
        st.bar_chart(status_counts, color="#00E5FF")

    with col2:
        st.markdown('<div class="fd-section">By Priority</div>', unsafe_allow_html=True)
        pri_counts: dict[str, int] = {}
        for t in tickets:
            pri_counts[t["priority"]] = pri_counts.get(t["priority"], 0) + 1
        st.bar_chart(pri_counts, color="#7C4DFF")

    st.markdown('<div class="fd-section">By Category</div>', unsafe_allow_html=True)
    cat_counts: dict[str, int] = {}
    for t in tickets:
        cat_counts[t["category"]] = cat_counts.get(t["category"], 0) + 1
    st.bar_chart(cat_counts, color="#4CD97B")


def _show_ticket_detail(ticket_id: int) -> None:
    ticket = db.get_ticket(ticket_id)
    if not ticket:
        st.error(f"Ticket #{ticket_id} not found.")
        return

    st.markdown(f"**#{ticket['ticket_id']} — {ticket['title']}**")

    col1, col2, col3 = st.columns(3)
    col1.metric("Status", ticket["status"])
    col2.metric("Priority", ticket["priority"])
    col3.metric("Category", ticket["category"])

    col4, col5 = st.columns(2)
    col4.metric("Assigned Dept", ticket.get("assigned_dept") or "—")
    sla = ticket.get("sla_deadline", "")
    col5.metric("SLA Deadline", sla[:16].replace("T", " ") if sla else "—")

    with st.expander("Description"):
        st.write(ticket["description"])

    st.markdown("**Change Status**")
    new_status = st.selectbox(
        "New status",
        ["Open", "Assigned", "In Progress", "Resolved", "Escalated", "Closed", "Reopened"],
        index=["Open", "Assigned", "In Progress", "Resolved", "Escalated", "Closed", "Reopened"].index(
            ticket["status"]
        ) if ticket["status"] in ["Open", "Assigned", "In Progress", "Resolved", "Escalated", "Closed", "Reopened"] else 0,
        key=f"admin_status_{ticket_id}",
    )
    if st.button("Apply Status Change", key=f"admin_apply_{ticket_id}"):
        if new_status != ticket["status"]:
            update = TicketUpdate(status=new_status)
            if new_status == "Resolved":
                update = TicketUpdate(status=new_status, resolved_at=datetime.now(timezone.utc).isoformat())
            elif new_status == "Closed":
                update = TicketUpdate(status=new_status, closed_at=datetime.now(timezone.utc).isoformat())
            db.update_ticket(ticket_id, update)
            st.success(f"Status updated to {new_status}.")
            st.rerun()
        else:
            st.warning("Status unchanged.")

    events = db.get_events_by_ticket(ticket_id)
    show_event_timeline(events)


def _run_escalation_check() -> int:
    overdue = db.get_overdue_tickets()
    count = 0
    for t in overdue:
        if t["status"] != "Escalated":
            db.update_ticket(t["ticket_id"], TicketUpdate(status="Escalated"))
            db.create_notification(NotificationCreate(
                ticket_id=t["ticket_id"],
                recipient=t["telegram_id"],
                channel="dashboard",
                message=f"Ticket #{t['ticket_id']} has been escalated due to SLA breach.",
                status="pending",
            ))
            count += 1
    return count
