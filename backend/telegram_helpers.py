"""Telegram Bot API helper utilities for FlowDesk.

Provides thin wrappers around the Telegram ``sendMessage`` endpoint and
convenience formatters for user-facing ticket replies.
"""

from __future__ import annotations

import os

import httpx


def send_message(chat_id: str, text: str) -> bool:
    """Send a text message to a Telegram chat.

    Uses the ``TELEGRAM_BOT_TOKEN`` environment variable to authenticate
    with the Telegram Bot API.

    Parameters
    ----------
    chat_id:
        The Telegram chat / user ID to send the message to.
    text:
        The message body (plain text or Markdown).

    Returns
    -------
    bool
        ``True`` if the Telegram API returned a success response,
        ``False`` otherwise.
    """
    raise NotImplementedError("Not yet implemented")


def format_ticket_reply(
    ticket_id: int,
    category: str,
    priority: str,
    sla_deadline: str,
) -> str:
    """Format a human-readable confirmation message for a new ticket.

    Parameters
    ----------
    ticket_id:
        The newly created ticket's database ID.
    category:
        The classified complaint category.
    priority:
        The assigned priority level.
    sla_deadline:
        ISO-8601 datetime string for the SLA deadline.

    Returns
    -------
    str
        A user-friendly, Markdown-formatted reply string.
    """
    return (
        f"🎫 *Ticket #{ticket_id} Created Successfully*\n\n"
        f"• *Category:* {category}\n"
        f"• *Priority:* {priority}\n"
        f"• *SLA Deadline:* {sla_deadline}\n\n"
        f"We have assigned this ticket to the responsible department and will resolve it shortly."
    )

