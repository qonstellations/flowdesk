import streamlit as st

_ACTION_ICON = {
    "TICKET_CREATED": "🎫",
    "CLASSIFIED": "🏷️",
    "ROUTED": "📍",
    "SLA_ASSIGNED": "⏰",
    "TARGET_RESOLUTION_SET": "⏰",
    "STATUS_UPDATED": "🔄",
    "ESCALATED": "🚨",
    "RESOLVED": "✅",
    "REOPENED": "🔁",
    "CLOSED": "🔒",
}
_ACTOR_COLOR = {
    "student": "#00E5FF",
    "staff": "#4CD97B",
    "admin": "#7C4DFF",
    "agent": "#FFB347",
    "system": "#8A94B0",
}


def show_event_timeline(events: list) -> None:
    st.markdown("#### Event Timeline")

    if not events:
        st.info("No events recorded yet.")
        return

    for ev in events:
        action = ev.get("action", "")
        icon = _ACTION_ICON.get(action, "📌")
        actor_type = ev.get("actor_type", "system")
        actor_name = ev.get("actor_name", "System")
        details = ev.get("details", "")
        raw_ts = ev.get("created_at", ev.get("timestamp", ""))
        ts = raw_ts[:16].replace("T", " ") if raw_ts else ""
        color = _ACTOR_COLOR.get(actor_type, "#8A94B0")

        st.html(
            f"""
            <div style="display:flex;gap:12px;align-items:flex-start;
                        margin-bottom:10px;padding:10px 14px;
                        background:rgba(20,26,46,0.5);border-radius:8px;
                        border-left:3px solid {color};">
                <div style="font-size:1.2rem;margin-top:1px;">{icon}</div>
                <div style="flex:1;">
                    <div style="display:flex;justify-content:space-between;">
                        <b style="color:#E8ECF5;font-size:0.9rem;">{action.replace('_', ' ')}</b>
                        <span style="color:#8A94B0;font-size:0.78rem;">{ts}</span>
                    </div>
                    <span style="color:{color};font-size:0.78rem;">{actor_name}</span>
                    {"" if not details else f'<br><span style="color:#8A94B0;font-size:0.8rem;">{details}</span>'}
                </div>
            </div>
            """
        )
