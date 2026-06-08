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

_CATEGORY_RATIONALE = {
    "IT & Wi-Fi":          "Complaint contains keywords related to network connectivity, internet access, or device/hardware failure.",
    "Hostel Maintenance":  "Complaint describes a physical defect or equipment failure inside hostel rooms or hostel common areas.",
    "Campus Maintenance":  "Complaint relates to campus-wide infrastructure — buildings, grounds, pathways, or shared utilities.",
    "Mess & Food":         "Complaint concerns the quality, hygiene, timing, or quantity of food served in the dining hall.",
    "Academics":           "Complaint involves examinations, coursework, faculty conduct, or academic administrative services.",
    "Other":               "Complaint did not match a primary category; routed to General Admin for manual triage.",
}

_PRIORITY_RATIONALE = {
    "Critical": "Affects safety or blocks a large group — SLA window is 4 hours.",
    "High":     "Significant disruption to daily student life — SLA window is 12 hours.",
    "Medium":   "Moderate inconvenience with a workaround available — SLA window is 24 hours.",
    "Low":      "Minor issue with no immediate risk or urgency — SLA window is 72 hours.",
}

_ROUTING_RATIONALE = {
    "IT Department":          "Handles all network, hardware, and digital infrastructure requests campus-wide.",
    "Hostel Maintenance Team":"On-site crew responsible for hostel room fixtures, plumbing, and electrical upkeep.",
    "Campus Facilities Team": "Manages campus buildings, grounds, and shared utilities outside hostel blocks.",
    "Mess Committee":         "Oversees dining hall operations, vendor contracts, and food hygiene standards.",
    "Academic Office":        "Coordinates academic scheduling, faculty matters, and examination logistics.",
    "General Admin":          "Handles miscellaneous requests not covered by any specialist department.",
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
            <div style="background:rgba(20,26,46,0.7);border-radius:10px 10px 0 0;padding:14px 18px 14px;
                        border-left:4px solid {border};border-bottom:none;">
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

        with st.expander("🤖 Why did the AI classify this?"):
            _render_ai_rationale(t)

        # Bottom spacer between cards
        st.markdown("<div style='margin-bottom:6px;'></div>", unsafe_allow_html=True)


def _render_ai_rationale(t: dict) -> None:
    cat   = t.get("category", "Other")
    pri   = t.get("priority", "Medium")
    dept  = t.get("assigned_dept") or ""
    pc    = _PRIORITY_COLOR.get(pri, "#00E5FF")

    st.markdown(
        f"""
        <div style="background:rgba(12,18,34,0.6);border-radius:0 0 10px 10px;
                    padding:14px 18px;border-left:4px solid rgba(124,77,255,0.5);
                    border-top:1px solid rgba(124,77,255,0.15);">
            <div style="font-size:0.78rem;color:#7C4DFF;font-weight:700;
                        letter-spacing:0.1em;text-transform:uppercase;margin-bottom:10px;">
                AI Classification Report
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;">
                <div>
                    <div style="font-size:0.72rem;color:#5A6480;text-transform:uppercase;
                                letter-spacing:0.1em;margin-bottom:3px;">Category</div>
                    <div style="color:#C8D0E8;font-weight:600;font-size:0.88rem;margin-bottom:4px;">
                        {cat}
                    </div>
                    <div style="color:#6A748A;font-size:0.78rem;line-height:1.4;">
                        {_CATEGORY_RATIONALE.get(cat, "")}
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
                            letter-spacing:0.1em;margin-bottom:3px;">Routed to</div>
                <div style="color:#C8D0E8;font-weight:600;font-size:0.88rem;margin-bottom:4px;">
                    {dept}
                </div>
                <div style="color:#6A748A;font-size:0.78rem;line-height:1.4;">
                    {_ROUTING_RATIONALE.get(dept, "")}
                </div>
            </div>'''}
        </div>
        """,
        unsafe_allow_html=True,
    )
