"""Reusable metrics bar component for FlowDesk.

Renders a row of metric cards using Streamlit columns, suitable for
dashboard summary displays.
"""

import streamlit as st


def render_metrics_bar(metrics: dict) -> None:
    """Render metric cards arranged in columns.

    Args:
        metrics: A dictionary mapping metric labels to their values.
    """
    pass

# temp test — delete later
render_metrics_bar({"Open": 2, "Escalated": 1, "Resolved": 1})