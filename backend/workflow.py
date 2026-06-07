"""LangGraph agentic workflow for FlowDesk ticket processing.

Defines the node functions that compose the complaint-handling pipeline
and exposes ``build_graph`` / ``run_workflow`` as the public API.
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph
from langgraph.graph.graph import CompiledGraph

from backend import classifier, db, router, sla
from backend.models import GraphState


# ── Graph nodes ────────────────────────────────────────────────────────


def intake_node(state: GraphState) -> GraphState:
    """Parse and normalise the incoming raw message.

    Responsibilities:
    - Extract or look up the student from ``state["telegram_id"]``
    - Populate ``title``, ``description``, ``student_id``
    - Set initial ``status`` to ``"Open"``
    """
    raise NotImplementedError("Not yet implemented")


def classification_node(state: GraphState) -> GraphState:
    """Classify the complaint using the LLM classifier.

    Populates ``category`` and ``priority`` in the state.
    """
    raise NotImplementedError("Not yet implemented")


def routing_node(state: GraphState) -> GraphState:
    """Route the ticket to the appropriate department.

    Populates ``assigned_dept`` in the state.
    """
    raise NotImplementedError("Not yet implemented")


def sla_node(state: GraphState) -> GraphState:
    """Calculate the SLA deadline for the ticket.

    Populates ``sla_deadline`` in the state.
    """
    raise NotImplementedError("Not yet implemented")


def work_order_node(state: GraphState) -> GraphState:
    """Persist the fully-enriched ticket to the database.

    Creates the ticket record, updates ``ticket_id`` in state, and
    queues a confirmation notification.
    """
    raise NotImplementedError("Not yet implemented")


# ── Graph construction ─────────────────────────────────────────────────


def build_graph() -> CompiledGraph:
    """Construct and compile the LangGraph state-machine.

    Node order::

        intake → classification → routing → sla → work_order → END

    Returns
    -------
    CompiledGraph
        The compiled, ready-to-invoke LangGraph graph.
    """
    raise NotImplementedError("Not yet implemented")


# ── Convenience runner ─────────────────────────────────────────────────


def run_workflow(
    raw_message: str,
    telegram_id: str | None = None,
) -> GraphState:
    """Run the full ticket-processing pipeline end-to-end.

    Parameters
    ----------
    raw_message:
        The user's raw complaint text.
    telegram_id:
        Optional Telegram user ID for attribution.

    Returns
    -------
    GraphState
        The final state dict after all nodes have executed.
    """
    raise NotImplementedError("Not yet implemented")
