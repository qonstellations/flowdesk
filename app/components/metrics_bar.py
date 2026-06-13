import streamlit as st

_LABEL_COLORS = {
    "Open": "#00E5FF",
    "Escalated": "#FF4D6D",
    "Resolved": "#4CD97B",
    "Closed": "#8A94B0",
    "In Progress": "#FFB347",
    "Assigned": "#FF8C00",
    "Reopened": "#B39DDB",
    "Total": "#7C4DFF",
    "Overdue": "#FF4D6D",
}


def render_metrics_bar(metrics: dict) -> None:
    total = metrics.get("Total", 1) or 1
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics.items()):
        color = _LABEL_COLORS.get(label, "#00E5FF")
        pct = 100 if label == "Total" else min(100, round(value / total * 100))
        col.html(
            f'<div class="metric-card">'
            f'<div class="metric-value" style="color:{color};text-shadow:0 0 12px {color}80;">{value}</div>'
            f'<div class="metric-label" style="color:#9AAAC8;">{label}</div>'
            f'<div style="height:3px;background:rgba(255,255,255,0.07);border-radius:2px;margin-top:10px;overflow:hidden;">'
            f'<div style="height:100%;width:{pct}%;background:{color};border-radius:2px;opacity:0.75;'
            f'transition:width 0.4s ease;"></div>'
            f'</div>'
            f'</div>'
        )
        active = st.session_state.get("metrics_filter") == label
        btn_label = "▴ Close" if active else "▾ View"
        if col.button(btn_label, key=f"metric_btn_{label}", use_container_width=True):
            if active:
                st.session_state.pop("metrics_filter", None)
            else:
                st.session_state["metrics_filter"] = label
            st.rerun()

    if all(v == 0 for v in metrics.values()):
        st.html(
            '<div style="text-align:center;padding:18px 0 6px;color:#8A94B8;font-size:0.88rem;">'
            '✦ No complaints yet — the campus is quiet.</div>'
        )
