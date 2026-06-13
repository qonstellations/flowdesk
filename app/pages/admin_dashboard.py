from datetime import datetime, timezone

import streamlit as st

import backend.db as db
from backend.escalation import escalate_overdue_tickets
from backend.models import TicketUpdate
from components.metrics_bar import render_metrics_bar
from components.ticket_detail import render_ticket_detail
from components.ticket_table import render_ticket_table, _PRIORITY_COLOR, _STATUS_COLOR



def render() -> None:
    st.markdown('<div class="fd-section">Admin Dashboard</div>', unsafe_allow_html=True)

    tickets = db.get_all_tickets()

    _show_metrics(tickets)
    _show_metrics_detail(tickets)
    st.markdown("---")

    col_target, col_refresh, col_space = st.columns([2, 1, 3])
    with col_target:
        if st.button("Escalated Tickets", use_container_width=True, type="primary"):
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
        ["All", "Open", "Assigned", "In Progress", "Escalated", "Resolved", "Reopened", "Closed", "Rejected"],
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
    _render_ticket_rows(filtered)


def _render_ticket_rows(filtered: list) -> None:
    if not filtered:
        st.html(
            '<div style="padding:32px;text-align:center;color:#5A6480;font-size:0.88rem;'
            'background:rgba(12,18,34,0.5);border-radius:12px;'
            'border:1px solid rgba(255,255,255,0.04);">'
            'No tickets here yet&#8202;&mdash; the campus is quiet.'
            '</div>'
        )
        return

    for t in filtered:
        tid      = int(t["ticket_id"])
        status   = t.get("status", "Open")
        priority = t.get("priority", "Medium")
        title    = t.get("title", "—")
        dept     = t.get("department_name") or t.get("assigned_dept") or "Unassigned"
        date     = (t.get("created_at") or "")[:10]
        sc       = _STATUS_COLOR.get(status, "#00E5FF")
        pc       = _PRIORITY_COLOR.get(priority, "#00E5FF")
        expanded = st.session_state.get("admin_expanded_ticket") == tid

        col_card, col_toggle = st.columns([8, 1])

        with col_card:
            st.html(
                f'<div style="background:rgba(20,26,46,0.7);border-radius:10px;padding:13px 16px;'
                f'border-left:4px solid {sc};">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                f'<div>'
                f'<span style="color:#7C4DFF;font-size:0.75rem;font-weight:700;">#{tid}</span>'
                f'<span style="color:#E8ECF5;font-size:0.9rem;font-weight:600;margin-left:8px;">{title}</span>'
                f'<br><span style="color:#8A94B0;font-size:0.75rem;margin-top:3px;display:inline-block;">'
                f'{dept}&nbsp;&middot;&nbsp;{date}</span>'
                f'</div>'
                f'<div style="display:flex;gap:6px;flex-shrink:0;margin-left:12px;">'
                f'<span style="color:{pc};padding:2px 8px;border-radius:20px;font-size:0.68rem;'
                f'font-weight:600;border:1px solid {pc}60;">{priority}</span>'
                f'<span style="color:{sc};padding:2px 8px;border-radius:20px;font-size:0.68rem;'
                f'font-weight:600;border:1px solid {sc}60;">{status}</span>'
                f'</div>'
                f'</div>'
                f'</div>'
            )

        with col_toggle:
            st.html("<div style='height:4px'></div>")
            if st.button("▲" if expanded else "▼", key=f"row_expand_{tid}", use_container_width=True):
                st.session_state["admin_expanded_ticket"] = None if expanded else tid
                st.rerun()

        if expanded:
            with st.container(border=True):
                _show_ticket_detail(tid)

        st.html(
            "<div style='height:1px;background:rgba(255,255,255,0.04);"
            "margin:4px 0 12px 0;'></div>"
        )


_TRIAGE_ACTIVE_STATUSES = {"Open", "Escalated", "Reopened"}


def _render_triage_rows(filtered: list) -> None:
    if not filtered:
        st.html(
            '<div style="padding:32px;text-align:center;color:#5A6480;font-size:0.88rem;'
            'background:rgba(12,18,34,0.5);border-radius:12px;'
            'border:1px solid rgba(255,255,255,0.04);">'
            'No tickets here yet&#8202;&mdash; the campus is quiet.'
            '</div>'
        )
        return

    for t in filtered:
        tid        = int(t["ticket_id"])
        status     = t.get("status", "Open")
        priority   = t.get("priority", "Medium")
        title      = t.get("title", "—")
        dept       = t.get("department_name") or t.get("assigned_dept") or "Unassigned"
        date       = (t.get("created_at") or "")[:10]
        sc         = _STATUS_COLOR.get(status, "#00E5FF")
        pc         = _PRIORITY_COLOR.get(priority, "#00E5FF")
        expanded   = st.session_state.get("triage_expanded_ticket") == tid
        can_triage = status in _TRIAGE_ACTIVE_STATUSES

        col_card, col_dtl, col_app, col_rej = st.columns([5, 1.5, 1, 1])

        with col_card:
            st.html(
                f'<div style="background:rgba(20,26,46,0.7);border-radius:10px;padding:13px 16px;'
                f'border-left:4px solid {sc};">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                f'<div>'
                f'<span style="color:#7C4DFF;font-size:0.75rem;font-weight:700;">#{tid}</span>'
                f'<span style="color:#E8ECF5;font-size:0.9rem;font-weight:600;margin-left:8px;">{title}</span>'
                f'<br><span style="color:#8A94B0;font-size:0.75rem;margin-top:3px;display:inline-block;">'
                f'{dept}&nbsp;&middot;&nbsp;{date}</span>'
                f'</div>'
                f'<div style="display:flex;gap:6px;flex-shrink:0;margin-left:12px;">'
                f'<span style="color:{pc};padding:2px 8px;border-radius:20px;font-size:0.68rem;'
                f'font-weight:600;border:1px solid {pc}60;">{priority}</span>'
                f'<span style="color:{sc};padding:2px 8px;border-radius:20px;font-size:0.68rem;'
                f'font-weight:600;border:1px solid {sc}60;">{status}</span>'
                f'</div>'
                f'</div>'
                f'</div>'
            )

        with col_dtl:
            st.html("<div style='height:4px'></div>")
            if st.button(
                "▲ Hide" if expanded else "▼ Details",
                key=f"triage_dtl_{tid}",
                use_container_width=True,
            ):
                st.session_state["triage_expanded_ticket"] = None if expanded else tid
                st.rerun()

        with col_app:
            st.html("<div style='height:4px'></div>")
            if st.button(
                "✓",
                key=f"triage_app_{tid}",
                use_container_width=True,
                type="primary",
                disabled=not can_triage,
                help="Approve — forward to department" if can_triage else f"Already {status}",
            ):
                db.update_ticket(tid, TicketUpdate(status="Assigned"))
                st.rerun()

        with col_rej:
            st.html("<div style='height:4px'></div>")
            if st.button(
                "✗",
                key=f"triage_rej_{tid}",
                use_container_width=True,
                disabled=not can_triage,
                help="Reject ticket" if can_triage else f"Already {status}",
            ):
                db.update_ticket(tid, TicketUpdate(status="Rejected"))
                st.rerun()

        if expanded:
            with st.container(border=True):
                _show_ticket_detail(tid)

        st.html(
            "<div style='height:1px;background:rgba(255,255,255,0.04);"
            "margin:4px 0 12px 0;'></div>"
        )


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


def _show_metrics_detail(tickets: list) -> None:
    active = st.session_state.get("metrics_filter")
    if not active:
        return

    now = datetime.now(timezone.utc)

    if active == "Total":
        filtered = tickets
    elif active == "Overdue":
        filtered = []
        for t in tickets:
            if t["status"] in ("Resolved", "Closed"):
                continue
            target = t.get("target_resolution_at") or t.get("sla_deadline")
            if not target:
                continue
            try:
                dl = datetime.fromisoformat(target)
                if dl.tzinfo is None:
                    dl = dl.replace(tzinfo=timezone.utc)
                if now > dl:
                    filtered.append(t)
            except Exception:
                pass
    else:
        filtered = [t for t in tickets if t.get("status") == active]

    st.html(
        f'<div style="font-size:0.72rem;color:#00E5FF;font-weight:700;letter-spacing:0.18em;'
        f'text-transform:uppercase;margin:12px 0 8px 0;">'
        f'{active} Tickets &mdash; {len(filtered)} found</div>'
    )
    _render_triage_rows(sorted(filtered, key=lambda x: x["created_at"], reverse=True))


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
