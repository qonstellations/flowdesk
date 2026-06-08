"""Telegram Bot API helper utilities for FlowDesk.

Provides thin wrappers around the Telegram ``sendMessage`` endpoint and
convenience formatters for user-facing ticket replies.
"""

from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}"


def _get_bot_token() -> str:
    """Return the bot token from the environment.

    Raises
    ------
    RuntimeError
        If ``TELEGRAM_BOT_TOKEN`` is not set.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not set. "
            "Get a token from @BotFather on Telegram and add it to your .env file."
        )
    return token


def send_message(chat_id: str, text: str, parse_mode: str = "Markdown") -> bool:
    """Send a text message to a Telegram chat.

    Uses the ``TELEGRAM_BOT_TOKEN`` environment variable to authenticate
    with the Telegram Bot API.

    Parameters
    ----------
    chat_id:
        The Telegram chat / user ID to send the message to.
    text:
        The message body (plain text or Markdown).
    parse_mode:
        Telegram parse mode. Defaults to ``"Markdown"``.

    Returns
    -------
    bool
        ``True`` if the Telegram API returned a success response,
        ``False`` otherwise.
    """
    token = _get_bot_token()
    url = f"{TELEGRAM_API_BASE.format(token=token)}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }

    try:
        response = httpx.post(url, json=payload, timeout=10.0)
        data = response.json()

        if data.get("ok"):
            logger.info("Message sent to chat_id=%s", chat_id)
            return True

        logger.warning(
            "Telegram API error for chat_id=%s: %s",
            chat_id,
            data.get("description", "Unknown error"),
        )
        return False

    except httpx.HTTPError as exc:
        logger.error("HTTP error sending message to chat_id=%s: %s", chat_id, exc)
        return False


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
    # Priority emoji mapping
    priority_emoji = {
        "Low": "🟢",
        "Medium": "🟡",
        "High": "🟠",
        "Critical": "🔴",
    }
    emoji = priority_emoji.get(priority, "⚪")

    return (
        f"✅ *Ticket Created Successfully!*\n"
        f"\n"
        f"🎫 *Ticket ID:* `#{ticket_id}`\n"
        f"📂 *Category:* {category}\n"
        f"{emoji} *Priority:* {priority}\n"
        f"⏰ *SLA Deadline:* {sla_deadline}\n"
        f"\n"
        f"Your complaint has been received and is being processed. "
        f"You will be notified when there are updates.\n"
        f"\n"
        f"Use /status to check your ticket status."
    )


def send_typing_action(chat_id: str) -> None:
    """Send a 'typing' chat action indicator to the user.

    This gives visual feedback that the bot is processing the message.

    Parameters
    ----------
    chat_id:
        The Telegram chat / user ID.
    """
    token = _get_bot_token()
    url = f"{TELEGRAM_API_BASE.format(token=token)}/sendChatAction"

    try:
        httpx.post(
            url,
            json={"chat_id": chat_id, "action": "typing"},
            timeout=5.0,
        )
    except httpx.HTTPError:
        # Non-critical — swallow silently
        pass


async def set_webhook(webhook_url: str) -> dict:
    """Register a webhook URL with the Telegram Bot API.

    Parameters
    ----------
    webhook_url:
        The public HTTPS URL that Telegram will POST updates to.
        Must end with your webhook path (e.g. ``https://yourdomain.com/webhook``).

    Returns
    -------
    dict
        The raw Telegram API response.
    """
    token = _get_bot_token()
    url = f"{TELEGRAM_API_BASE.format(token=token)}/setWebhook"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(url, json={"url": webhook_url})
        return response.json()


async def delete_webhook() -> dict:
    """Remove the current webhook so you can use polling instead.

    Returns
    -------
    dict
        The raw Telegram API response.
    """
    token = _get_bot_token()
    url = f"{TELEGRAM_API_BASE.format(token=token)}/deleteWebhook"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(url)
        return response.json()
