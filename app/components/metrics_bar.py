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
