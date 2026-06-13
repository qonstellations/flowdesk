"""Shared ticket detail component for FlowDesk.

render_ticket_detail(ticket, events, role) is the single source of truth
for the full ticket view used by admin, staff, and student pages.
All values read from backend.constants — no hardcoded enums.
All writes go through db.update_ticket(TicketUpdate(...)).
"""

from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

import backend.db as db
from backend import constants
from backend.models import TicketUpdate
from components.event_timeline import show_event_timeline

# ── Style constants ────────────────────────────────────────────────────────

_PRIORITY_COLOR = {
    "Low": "#00E5FF",
    "Medium": "#FFD700",
    "High": "#FF8C00",
    "Critical": "#FF4D6D",
}
_STATUS_COLOR = {
    "Open": "#00E5FF",
    "Assigned": "#FF8C00",
    "In Progress": "#FFB347",
    "Resolved": "#4CD97B",
    "Escalated": "#FF4D6D",
    "Closed": "#8A94B0",
    "Reopened": "#B39DDB",
}

# Staff may only move a ticket along these edges
_STAFF_TRANSITIONS: dict[str, list[str]] = {
    "Open":        ["In Progress"],
    "Assigned":    ["In Progress"],
    "In Progress": ["Resolved"],
    "Resolved":    ["Closed", "Reopened"],
    "Reopened":    ["In Progress"],
    "Escalated":   ["In Progress", "Resolved"],
    "Closed":      [],
}


# ── Helpers ────────────────────────────────────────────────────────────────

def _fmt_ts(iso: str | None, show_time: bool = True) -> str:
    if not iso:
        return "—"
    try:
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.strftime("%d %b %Y, %H:%M") if show_time else dt.strftime("%d %b %Y")
    except Exception:
        return iso[:16].replace("T", " ")


def _is_overdue(ticket: dict) -> bool:
    target = ticket.get("target_resolution_at") or ticket.get("sla_deadline")
    if not target or ticket.get("status") in ("Resolved", "Closed"):
        return False
    try:
        dl = datetime.fromisoformat(target)
        if dl.tzinfo is None:
            dl = dl.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) > dl
    except Exception:
        return False


def _badge(text: str, color: str) -> str:
    return (
        f'<span style="color:{color};padding:3px 12px;border-radius:20px;'
        f'font-size:0.78rem;font-weight:700;border:1px solid {color}60;'
        f'background:{color}12;white-space:nowrap;">{text}</span>'
    )


def _meta_cell(label: str, value: str, color: str = "#C8D0E8") -> str:
    return (
        f'<div style="margin-bottom:14px;">'
        f'<div style="font-size:0.68rem;color:#5A6480;text-transform:uppercase;'
        f'letter-spacing:0.1em;margin-bottom:3px;">{label}</div>'
        f'<div style="font-size:0.88rem;font-weight:600;color:{color};">{value}</div>'
        f'</div>'
    )


# ── Public API ─────────────────────────────────────────────────────────────

def render_ticket_detail(
    ticket: dict,
    events: list[dict],
    role: str,
) -> None:
    """Render the full ticket detail panel.

    Parameters
    ----------
    ticket : dict
        Row dict from db.get_ticket().
    events : list[dict]
        Rows from db.get_events_by_ticket().
    role : str
        One of "admin" | "staff" | "student".  Controls which
        update controls are rendered.
    """
    tid      = ticket["ticket_id"]
    status   = ticket.get("status", "Open")
    priority = ticket.get("priority", "Medium")
    department = ticket.get("department_name") or ticket.get("assigned_dept") or "Unassigned"
    sc = _STATUS_COLOR.get(status, "#00E5FF")
    pc = _PRIORITY_COLOR.get(priority, "#00E5FF")
    overdue  = _is_overdue(ticket)

    # ── Section 1: Header ─────────────────────────────────────────────────
    st.html(
        f"""
        <div style="background:rgba(14,22,48,0.8);border-radius:16px 16px 0 0;
                    padding:20px 24px 16px;
                    border-left:4px solid {'#FF4D6D' if overdue else sc};">
            <div style="font-size:0.72rem;color:#5A6480;letter-spacing:0.1em;
                        text-transform:uppercase;margin-bottom:6px;">
                Ticket #{tid}
            </div>
            <div style="font-size:1.2rem;font-weight:800;color:#E8ECF5;
                        line-height:1.3;margin-bottom:14px;">
                {ticket['title']}
            </div>
            <div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;">
                {_badge(status, '#FF4D6D' if overdue else sc)}
                {_badge(priority, pc)}
                {_badge(department, '#7C4DFF')}
                {'<span style="color:#FF4D6D;font-size:0.75rem;font-weight:700;'
                  'padding:3px 10px;border-radius:20px;border:1px solid #FF4D6D60;'
                  'background:#FF4D6D12;">⚠ TARGET OVERDUE</span>' if overdue else ''}
            </div>
        </div>
        """
    )

    # ── Section 2: Metadata grid ──────────────────────────────────────────
    left_html  = ""
    right_html = ""

    left_html  += _meta_cell("Submitted by",  ticket.get("telegram_id") or "—")
    left_html  += _meta_cell("Location",      ticket.get("location") or "Unknown")
    left_html  += _meta_cell("Assigned dept", department,
                              "#4CD97B" if department != "Unassigned" else "#5A6480")
    if ticket.get("routing_confidence") is not None:
        left_html += _meta_cell("Routing confidence", f"{float(ticket['routing_confidence']):.0%}", "#7C4DFF")

    target_val = _fmt_ts(ticket.get("target_resolution_at") or ticket.get("sla_deadline"))
    target_color = "#FF4D6D" if overdue else "#FFD700"
    right_html += _meta_cell("Created",     _fmt_ts(ticket.get("created_at")))
    right_html += _meta_cell("Last updated", _fmt_ts(ticket.get("updated_at")))
    right_html += _meta_cell("Target resolution", target_val, target_color)
    if ticket.get("resolved_at"):
        right_html += _meta_cell("Resolved at", _fmt_ts(ticket["resolved_at"]), "#4CD97B")
    if ticket.get("closed_at"):
        right_html += _meta_cell("Closed at",   _fmt_ts(ticket["closed_at"]),   "#8A94B0")

    st.html(
        f"""
        <div style="background:rgba(10,16,34,0.7);padding:18px 24px;
                    border-left:4px solid {'#FF4D6D' if overdue else sc};
                    border-top:1px solid rgba(255,255,255,0.04);">
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:0 32px;">
                <div>{left_html}</div>
                <div>{right_html}</div>
            </div>
        </div>
        """
    )

    # ── Section 3: Description ────────────────────────────────────────────
    with st.expander("📄 Full Description", expanded=False):
        st.html(
            f"""
            <div style="color:#C8D0E8;font-size:0.9rem;line-height:1.7;
                        padding:4px 0;">
                {ticket.get('description', '—')}
            </div>
            """
        )

    if ticket.get("routing_reason"):
        with st.expander("Routing Reason", expanded=False):
            st.write(ticket["routing_reason"])

    # ── Section 4: Update controls ────────────────────────────────────────
    st.html(
        '<div style="background:rgba(12,18,34,0.6);border-radius:0 0 16px 16px;'
        'padding:18px 24px;border-left:4px solid rgba(124,77,255,0.4);'
        'border-top:1px solid rgba(255,255,255,0.04);">'
    )

    if role == "admin":
        _admin_controls(ticket, tid, status)
    elif role == "staff":
        _staff_controls(ticket, tid, status)
    else:
        st.html(
            '<p style="color:#5A6480;font-size:0.85rem;margin:0;">'
            "Status updates are handled by the assigned department.</p>"
        )

    st.html("</div>")

    # ── Section 5: Event timeline ─────────────────────────────────────────
    st.html("<div style='margin-top:20px;'></div>")
    show_event_timeline(events)


# ── Role-specific control panels ───────────────────────────────────────────

def _admin_controls(ticket: dict, tid: int, current_status: str) -> None:
    st.html(
        '<div style="font-size:0.72rem;color:#7C4DFF;font-weight:700;'
        'letter-spacing:0.1em;text-transform:uppercase;margin-bottom:14px;">'
        "Admin Controls</div>"
    )

    col_s, col_d, col_b = st.columns([2, 2, 1])

    status_list = list(constants.STATUSES)
    current_idx = status_list.index(current_status) if current_status in status_list else 0
    new_status = col_s.selectbox(
        "Status",
        status_list,
        index=current_idx,
        key=f"detail_admin_status_{tid}",
    )

    departments = db.get_departments(include_inactive=False)
    dept_options = {"— no change —": None} | {
        dept["name"]: int(dept["department_id"]) for dept in departments
    }
    dept_list = list(dept_options.keys())
    new_dept   = col_d.selectbox(
        "Re-assign dept",
        dept_list,
        index=0,
        key=f"detail_admin_dept_{tid}",
    )

    col_b.html("<div style='margin-top:28px;'></div>")
    if col_b.button("Apply", key=f"detail_admin_apply_{tid}",
                    use_container_width=True, type="primary"):
        changed = False

        if new_status != current_status:
            now = datetime.now(timezone.utc).isoformat()
            update = TicketUpdate(
                status=new_status,
                resolved_at=now if new_status == "Resolved" else None,
                closed_at=now   if new_status == "Closed"   else None,
            )
            db.update_ticket(tid, update)
            changed = True

        if new_dept != "— no change —" and new_dept != (ticket.get("department_name") or ticket.get("assigned_dept")):
            db.update_ticket(tid, TicketUpdate(department_id=dept_options[new_dept]))
            changed = True

        if changed:
            st.success("Ticket updated.")
            st.rerun()
        else:
            st.info("Nothing changed.")


def _staff_controls(ticket: dict, tid: int, current_status: str) -> None:
    transitions = _STAFF_TRANSITIONS.get(current_status, [])

    st.html(
        '<div style="font-size:0.72rem;color:#4CD97B;font-weight:700;'
        'letter-spacing:0.1em;text-transform:uppercase;margin-bottom:14px;">'
        "Staff Actions</div>"
    )

    if not transitions:
        st.html(
            '<p style="color:#5A6480;font-size:0.85rem;margin:0;">'
            f"No further transitions available from <b>{current_status}</b>.</p>"
        )
        return

    col_s, col_b = st.columns([3, 1])
    new_status = col_s.selectbox(
        "Move to",
        transitions,
        key=f"detail_staff_status_{tid}",
    )
    col_b.html("<div style='margin-top:28px;'></div>")
    if col_b.button("✓ Update", key=f"detail_staff_apply_{tid}",
                    use_container_width=True, type="primary"):
        now = datetime.now(timezone.utc).isoformat()
        update = TicketUpdate(
            status=new_status,
            resolved_at=now if new_status == "Resolved" else None,
            closed_at=now   if new_status == "Closed"   else None,
        )
        db.update_ticket(tid, update)
        st.success(f"Ticket #{tid} moved to **{new_status}**.")
        st.rerun()
