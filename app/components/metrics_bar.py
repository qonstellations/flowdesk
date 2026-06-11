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
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics.items()):
        color = _LABEL_COLORS.get(label, "#00E5FF")
        col.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value" style="color:{color};text-shadow:0 0 12px {color}80;">{value}</div>
                <div class="metric-label">{label}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        active = st.session_state.get("metrics_filter") == label
        btn_label = f"▴ Close" if active else f"▾ View"
        if col.button(btn_label, key=f"metric_btn_{label}", use_container_width=True):
            if active:
                st.session_state.pop("metrics_filter", None)
            else:
                st.session_state["metrics_filter"] = label
            st.rerun()

    if all(v == 0 for v in metrics.values()):
        st.markdown(
            '<div style="text-align:center;padding:18px 0 6px;color:#5A6480;font-size:0.88rem;">'
            '✦ No complaints yet — the campus is quiet.</div>',
            unsafe_allow_html=True,
        )
