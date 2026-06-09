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

_PRIORITY_RATIONALE = {
    "Critical": "Affects safety or blocks a large group.",
    "High":     "Significant disruption to daily student life.",
    "Medium":   "Moderate inconvenience with a workaround available.",
    "Low":      "Minor issue with no immediate risk or urgency.",
}


def _is_overdue(target_resolution_at: str | None, status: str) -> bool:
    if not target_resolution_at or status in ("Resolved", "Closed"):
        return False
    try:
        dl = datetime.fromisoformat(target_resolution_at)
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
        target_at = t.get("target_resolution_at") or t.get("sla_deadline")
        overdue = _is_overdue(target_at, status)
        sc = _STATUS_COLOR.get(status, "#00E5FF")
        pc = _PRIORITY_COLOR.get(t.get("priority", "Low"), "#00E5FF")
        border = "#FF4D6D" if overdue else sc

        target_html = ""
        if target_at:
            if overdue:
                target_html = '<span style="color:#FF4D6D;font-size:0.75rem;font-weight:600;">⚠ TARGET OVERDUE</span>'
            else:
                dl_str = target_at[:16].replace("T", " ")
                target_html = f'<span style="color:#8A94B0;font-size:0.75rem;">Target: {dl_str}</span>'

        dept = t.get("department_name") or t.get("assigned_dept") or "Unassigned"
        date = t["created_at"][:10] if t.get("created_at") else ""

        st.markdown(
            f"""
            <div style="background:rgba(20,26,46,0.7);border-radius:10px 10px 0 0;padding:14px 18px 14px;
                        border-left:4px solid {border};border-bottom:none;">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                    <div>
                        <b style="color:#E8ECF5;font-size:0.95rem;">#{t['ticket_id']} {t['title']}</b><br>
                        <span style="color:#8A94B0;font-size:0.8rem;">{dept} · {date}</span><br>
                        {target_html}
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

        with st.expander("🤖 Routing and target details"):
            _render_ai_rationale(t)

        # Bottom spacer between cards
        st.markdown("<div style='margin-bottom:6px;'></div>", unsafe_allow_html=True)


def _render_ai_rationale(t: dict) -> None:
    pri   = t.get("priority", "Medium")
    dept  = t.get("department_name") or t.get("assigned_dept") or ""
    pc    = _PRIORITY_COLOR.get(pri, "#00E5FF")
    routing_reason = t.get("routing_reason") or "No routing reason recorded."
    confidence = t.get("routing_confidence")
    confidence_label = "—" if confidence is None else f"{float(confidence):.0%}"

    st.markdown(
        f"""
        <div style="background:rgba(12,18,34,0.6);border-radius:0 0 10px 10px;
                    padding:14px 18px;border-left:4px solid rgba(124,77,255,0.5);
                    border-top:1px solid rgba(124,77,255,0.15);">
            <div style="font-size:0.78rem;color:#7C4DFF;font-weight:700;
                        letter-spacing:0.1em;text-transform:uppercase;margin-bottom:10px;">
                AI Routing Report
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;">
                <div>
                    <div style="font-size:0.72rem;color:#5A6480;text-transform:uppercase;
                                letter-spacing:0.1em;margin-bottom:3px;">Department</div>
                    <div style="color:#C8D0E8;font-weight:600;font-size:0.88rem;margin-bottom:4px;">
                        {dept or 'Unassigned'}
                    </div>
                    <div style="color:#6A748A;font-size:0.78rem;line-height:1.4;">
                        {routing_reason}
                    </div>
                </div>
                <div>
                    <div style="font-size:0.72rem;color:#5A6480;text-transform:uppercase;
                                letter-spacing:0.1em;margin-bottom:3px;">Priority</div>
                    <div style="color:{pc};font-weight:600;font-size:0.88rem;margin-bottom:4px;">
                        {pri}
                    </div>
                    <div style="color:#6A748A;font-size:0.78rem;line-height:1.4;">
                        {_PRIORITY_RATIONALE.get(pri, "")}
                    </div>
                </div>
            </div>
            {"" if not dept else f'''
            <div style="margin-top:12px;padding-top:10px;border-top:1px solid rgba(255,255,255,0.05);">
                <div style="font-size:0.72rem;color:#5A6480;text-transform:uppercase;
                            letter-spacing:0.1em;margin-bottom:3px;">Routing confidence</div>
                <div style="color:#C8D0E8;font-weight:600;font-size:0.88rem;margin-bottom:4px;">
                    {confidence_label}
                </div>
            </div>'''}
        </div>
        """,
        unsafe_allow_html=True,
    )
