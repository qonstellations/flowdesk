from datetime import datetime, timezone

import streamlit as st

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


def _is_overdue(sla_deadline: str | None, status: str) -> bool:
    if not sla_deadline or status in ("Resolved", "Closed"):
        return False
    try:
        dl = datetime.fromisoformat(sla_deadline)
        if dl.tzinfo is None:
            dl = dl.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) > dl
    except Exception:
        return False


def render_ticket_table(tickets: list) -> None:
    if not tickets:
        st.info("No tickets found.")
        return

    for t in sorted(tickets, key=lambda x: x["created_at"], reverse=True):
        status = t.get("status", "Open")
        overdue = _is_overdue(t.get("sla_deadline"), status)
        sc = _STATUS_COLOR.get(status, "#00E5FF")
        pc = _PRIORITY_COLOR.get(t.get("priority", "Low"), "#00E5FF")
        border = "#FF4D6D" if overdue else sc

        sla_html = ""
        if t.get("sla_deadline"):
            if overdue:
                sla_html = '<span style="color:#FF4D6D;font-size:0.75rem;font-weight:600;">⚠ SLA OVERDUE</span>'
            else:
                dl_str = t["sla_deadline"][:16].replace("T", " ")
                sla_html = f'<span style="color:#8A94B0;font-size:0.75rem;">SLA: {dl_str}</span>'

        dept = t.get("assigned_dept") or "Unassigned"
        cat = t.get("category", "")
        date = t["created_at"][:10] if t.get("created_at") else ""

        st.markdown(
            f"""
            <div style="background:rgba(20,26,46,0.7);border-radius:10px;padding:14px 18px;
                        margin-bottom:8px;border-left:4px solid {border};">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                    <div>
                        <b style="color:#E8ECF5;font-size:0.95rem;">#{t['ticket_id']} {t['title']}</b><br>
                        <span style="color:#8A94B0;font-size:0.8rem;">{dept} · {cat} · {date}</span><br>
                        {sla_html}
                    </div>
                    <div style="display:flex;gap:8px;align-items:center;flex-shrink:0;margin-left:12px;">
                        <span style="color:{pc};padding:2px 9px;border-radius:20px;
                              font-size:0.7rem;font-weight:600;border:1px solid {pc}60;">
                            {t.get('priority','')}</span>
                        <span style="color:{sc};padding:2px 11px;border-radius:20px;
                              font-size:0.75rem;font-weight:600;border:1px solid {sc}60;">
                            {status}</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
