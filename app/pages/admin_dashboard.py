from datetime import datetime, timezone

import streamlit as st

import backend.db as db
from backend.escalation import escalate_overdue_tickets
from components.metrics_bar import render_metrics_bar
from components.ticket_detail import render_ticket_detail
from components.ticket_table import render_ticket_table



def render() -> None:
    st.markdown('<div class="fd-section">Admin Dashboard</div>', unsafe_allow_html=True)

    tickets = db.get_all_tickets()

    _show_metrics(tickets)
    st.markdown("---")

    col_target, col_refresh, col_space = st.columns([2, 1, 3])
    with col_target:
        if st.button("⚡ Trigger Escalation Check", use_container_width=True, type="primary"):
            count = escalate_overdue_tickets()
            if count:
                st.success(f"Escalated {count} overdue ticket(s).")
                st.rerun()
            else:
                st.info("No overdue tickets to escalate.")

    with col_refresh:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    st.markdown("---")

    tab_tickets, tab_departments, tab_analytics = st.tabs(["📋  All Tickets", "🏢 Departments", "📊  Analytics"])

    with tab_tickets:
        _show_all_tickets(tickets)

    with tab_departments:
        _show_department_manager()

    with tab_analytics:
        _show_analytics_charts(tickets)


def _show_metrics(tickets: list) -> None:
    total = len(tickets)
    counts = {s: 0 for s in ("Open", "Assigned", "In Progress", "Escalated", "Resolved", "Closed")}
    overdue = 0
    now = datetime.now(timezone.utc)
    for t in tickets:
        counts[t["status"]] = counts.get(t["status"], 0) + 1
        target_at = t.get("target_resolution_at") or t.get("sla_deadline")
        if target_at and t["status"] not in ("Resolved", "Closed"):
            try:
                dl = datetime.fromisoformat(target_at)
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

    col_s, col_d, col_p = st.columns(3)
    status_filter = col_s.selectbox(
        "Filter by status",
        ["All", "Open", "Assigned", "In Progress", "Escalated", "Resolved", "Reopened", "Closed"],
        key="admin_status_filter",
    )
    department_names = sorted({
        t.get("department_name") or t.get("assigned_dept") or "Unassigned"
        for t in tickets
    })
    department_filter = col_d.selectbox(
        "Filter by department",
        ["All"] + department_names,
        key="admin_dept_filter",
    )
    priority_filter = col_p.selectbox(
        "Filter by priority",
        ["All", "Critical", "High", "Medium", "Low"],
        key="admin_pri_filter",
    )

    filtered = tickets
    if status_filter != "All":
        filtered = [t for t in filtered if t["status"] == status_filter]
    if department_filter != "All":
        filtered = [
            t for t in filtered
            if (t.get("department_name") or t.get("assigned_dept") or "Unassigned") == department_filter
        ]
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

    st.markdown('<div class="fd-section">By Department</div>', unsafe_allow_html=True)
    dept_counts: dict[str, int] = {}
    for t in tickets:
        dept = t.get("department_name") or t.get("assigned_dept") or "Unassigned"
        dept_counts[dept] = dept_counts.get(dept, 0) + 1
    st.bar_chart(dept_counts, color="#4CD97B")


def _show_ticket_detail(ticket_id: int) -> None:
    ticket = db.get_ticket(ticket_id)
    if not ticket:
        st.error(f"Ticket #{ticket_id} not found.")
        return
    events = db.get_events_by_ticket(ticket_id)
    render_ticket_detail(ticket, events, role="admin")


def _show_department_manager() -> None:
    st.markdown('<div class="fd-section">Department Management</div>', unsafe_allow_html=True)
    departments = db.get_departments(include_inactive=True)

    with st.form("department_create", clear_on_submit=True):
        st.subheader("Create Department")
        name = st.text_input("Name", placeholder="General Admin")
        responsibilities = st.text_area("Responsibilities", height=90)
        col_contact, col_email = st.columns(2)
        contact = col_contact.text_input("Contact")
        escalation_contact = col_email.text_input("Email ID", placeholder="Escalation email")
        if st.form_submit_button("Create Department", type="primary"):
            if not name.strip():
                st.error("Department name is required.")
            else:
                db.create_department(
                    name.strip(),
                    responsibilities.strip(),
                    contact.strip(),
                    escalation_contact.strip(),
                )
                st.success("Department created.")
                st.rerun()

    st.markdown("---")
    if not departments:
        st.info("No departments configured yet. Add at least one active department before accepting tickets.")
        return

    for dept in departments:
        with st.expander(f"{'Active' if dept.get('active') else 'Inactive'} · {dept['name']}"):
            with st.form(f"department_edit_{dept['department_id']}"):
                name = st.text_input("Name", value=dept["name"], key=f"name_{dept['department_id']}")
                responsibilities = st.text_area("Responsibilities", value=dept.get("responsibilities") or "", height=90, key=f"resp_{dept['department_id']}")
                col_contact, col_email, col_active = st.columns([2, 2, 1])
                contact = col_contact.text_input("Contact", value=dept.get("contact") or "", key=f"contact_{dept['department_id']}")
                escalation_contact = col_email.text_input("Email ID", value=dept.get("escalation_contact") or "", key=f"esc_{dept['department_id']}")
                active = col_active.checkbox("Active", value=bool(dept.get("active")), key=f"active_{dept['department_id']}")
                if st.form_submit_button("Save"):
                    db.update_department(
                        int(dept["department_id"]),
                        name.strip(),
                        responsibilities.strip(),
                        contact.strip(),
                        escalation_contact.strip(),
                        active,
                    )
                    st.success("Department updated.")
                    st.rerun()
