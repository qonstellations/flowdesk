"""FastAPI webhook endpoint for the FlowDesk Telegram bot.

Exposes a single ``POST /webhook`` route that Telegram calls for every
incoming message.  The handler parses the update, runs the workflow,
and returns a JSON acknowledgement.

Startup events:
- Initialises the SQLite database.
- Optionally registers the Telegram webhook (if ``TELEGRAM_WEBHOOK_URL`` is set).
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend import db, telegram_helpers

# Load .env file so TELEGRAM_BOT_TOKEN, TELEGRAM_WEBHOOK_URL, etc. are available
load_dotenv()

logger = logging.getLogger(__name__)


# ── Lifespan ────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Run startup / shutdown tasks for the FastAPI app."""
    # ── Startup ──
    logger.info("Initialising database …")
    db.init_db()

    # If a public webhook URL is configured, register it with Telegram
    webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL", "").strip()
    if webhook_url:
        full_url = webhook_url.rstrip("/") + "/webhook"
        logger.info("Registering Telegram webhook → %s", full_url)
        result = await telegram_helpers.set_webhook(full_url)
        if result.get("ok"):
            logger.info("Telegram webhook registered successfully.")
        else:
            logger.warning("Telegram webhook registration failed: %s", result)
    else:
        logger.warning(
            "TELEGRAM_WEBHOOK_URL not set — skipping webhook registration. "
            "Set it in .env to enable automatic webhook setup."
        )

    yield  # ── Application runs here ──

    # ── Shutdown ──
    logger.info("FlowDesk webhook server shutting down.")


# ── FastAPI app ─────────────────────────────────────────────────────────


app = FastAPI(
    title="FlowDesk Telegram Webhook",
    description="Receives Telegram bot updates and processes campus complaints.",
    version="0.1.0",
    lifespan=lifespan,
)


# ── Health check ────────────────────────────────────────────────────────


@app.get("/health")
async def health_check() -> dict:
    """Simple health-check endpoint.

    Returns ``{"status": "ok"}`` so monitoring tools can verify the
    server is alive.
    """
    return {"status": "ok"}


# ── Webhook route ───────────────────────────────────────────────────────


@app.post("/webhook")
async def telegram_webhook(request: Request) -> JSONResponse:
    """Handle an incoming Telegram update.

    Parses the update payload, extracts the user's message, triggers the
    complaint-processing workflow, and sends back a Telegram reply.

    Returns
    -------
    JSONResponse
        ``{"status": "ok"}`` on success, or an error payload.
    """
    try:
        data = await request.json()
    except Exception:
        logger.error("Failed to parse webhook JSON body.")
        return JSONResponse(
            status_code=400,
            content={"status": "error", "detail": "Invalid JSON"},
        )

    logger.info("Received Telegram update: %s", data.get("update_id", "?"))

    # ── Extract message data ──
    try:
        telegram_id, message_text, chat_id, user_name = _parse_telegram_update(data)
    except ValueError as exc:
        logger.warning("Ignoring update — %s", exc)
        # Telegram expects 200 even for updates we skip
        return JSONResponse(content={"status": "ok", "detail": str(exc)})

    # ── Handle bot commands ──
    if message_text.startswith("/"):
        await _handle_command(message_text, telegram_id, chat_id, user_name)
        return JSONResponse(content={"status": "ok"})

    # ── Show typing indicator while processing ──
    telegram_helpers.send_typing_action(chat_id)

    # ── Auto-register user if first time ──
    _ensure_user_exists(telegram_id, user_name)

    # ── Run the agentic workflow ──
    try:
        from backend.workflow import run_workflow

        final_state = run_workflow(
            raw_message=message_text,
            telegram_id=telegram_id,
        )
    except Exception as exc:
        logger.exception("Workflow failed for telegram_id=%s", telegram_id)
        telegram_helpers.send_message(
            chat_id,
            "⚠️ Sorry, something went wrong processing your complaint. "
            "Please try again or contact the admin directly.",
        )
        return JSONResponse(content={"status": "error", "detail": str(exc)})

    # ── Send confirmation reply to the student ──
    ticket_id = final_state.get("ticket_id")
    category = final_state.get("category", "Unknown")
    priority = final_state.get("priority", "Medium")
    sla_deadline = final_state.get("sla_deadline", "TBD")

    reply = telegram_helpers.format_ticket_reply(
        ticket_id=ticket_id,
        category=category,
        priority=priority,
        sla_deadline=sla_deadline,
    )
    telegram_helpers.send_message(chat_id, reply)

    logger.info(
        "Ticket #%s created for telegram_id=%s (category=%s, priority=%s)",
        ticket_id,
        telegram_id,
        category,
        priority,
    )

    return JSONResponse(content={"status": "ok", "ticket_id": ticket_id})


# ── Internal helpers ────────────────────────────────────────────────────


def _parse_telegram_update(data: dict) -> tuple[str, str, str, str]:
    """Extract the Telegram user ID, message text, chat ID, and user name.

    Parameters
    ----------
    data:
        The raw JSON body of the Telegram webhook callback.

    Returns
    -------
    tuple[str, str, str, str]
        ``(telegram_id, message_text, chat_id, user_name)``

    Raises
    ------
    ValueError
        If the update does not contain a usable text message.
    """
    # Telegram sends different shapes for messages, edited messages, etc.
    message = data.get("message") or data.get("edited_message")

    if not message:
        raise ValueError("Update contains no message or edited_message.")

    text = message.get("text", "").strip()
    if not text:
        raise ValueError("Message contains no text content.")

    chat = message.get("chat", {})
    chat_id = str(chat.get("id", ""))
    if not chat_id:
        raise ValueError("Message contains no chat ID.")

    from_user = message.get("from", {})
    telegram_id = str(from_user.get("id", ""))
    if not telegram_id:
        raise ValueError("Message contains no sender ID.")

    # Build a display name from available fields
    first_name = from_user.get("first_name", "")
    last_name = from_user.get("last_name", "")
    user_name = f"{first_name} {last_name}".strip() or from_user.get("username", "Unknown")

    return telegram_id, text, chat_id, user_name


def _ensure_user_exists(telegram_id: str, name: str) -> None:
    """Create a user record if one doesn't already exist for this Telegram ID.

    Parameters
    ----------
    telegram_id:
        The Telegram user ID.
    name:
        The user's display name from Telegram.
    """
    existing = db.get_user_by_telegram_id(telegram_id)
    if existing is None:
        from backend.models import UserCreate

        db.create_user(
            UserCreate(
                name=name,
                role="student",
                telegram_id=telegram_id,
            )
        )
        logger.info("Auto-registered new student: telegram_id=%s, name=%s", telegram_id, name)


async def _handle_command(
    message_text: str,
    telegram_id: str,
    chat_id: str,
    user_name: str,
) -> None:
    """Handle slash commands from the user.

    Supported commands:

    - ``/start`` — Welcome message
    - ``/help``  — Usage instructions
    - ``/status`` — Show the user's recent tickets

    Parameters
    ----------
    message_text:
        The full message text (starts with ``/``).
    telegram_id:
        The sender's Telegram user ID.
    chat_id:
        The chat to reply to.
    user_name:
        The sender's display name.
    """
    command = message_text.split()[0].lower()

    if command in ("/start", "/start@flowdeskbot"):
        telegram_helpers.send_message(
            chat_id,
            f"👋 *Welcome to FlowDesk, {user_name}!*\n"
            f"\n"
            f"I'm your campus complaint assistant. Just send me a message "
            f"describing your issue, and I'll create a tracked ticket for you.\n"
            f"\n"
            f"*Examples:*\n"
            f"• _Wi-Fi is not working in Hostel Block A_\n"
            f"• _Water leakage in Room 204_\n"
            f"• _Mess food quality has been poor this week_\n"
            f"\n"
            f"Type /help for more info.",
        )
        # Auto-register on /start
        _ensure_user_exists(telegram_id, user_name)

    elif command in ("/help", "/help@flowdeskbot"):
        telegram_helpers.send_message(
            chat_id,
            "ℹ️ *FlowDesk Help*\n"
            "\n"
            "Just type your complaint as a normal message and I'll handle the rest!\n"
            "\n"
            "*Commands:*\n"
            "/start — Welcome message\n"
            "/help — This help text\n"
            "/status — Check your recent tickets\n"
            "\n"
            "*How it works:*\n"
            "1️⃣ You describe the issue\n"
            "2️⃣ AI classifies & routes it\n"
            "3️⃣ You get a ticket ID + SLA deadline\n"
            "4️⃣ Staff resolves the issue\n"
            "5️⃣ You get notified when it's done",
        )

    elif command in ("/status", "/status@flowdeskbot"):
        tickets = db.get_tickets_by_telegram_id(telegram_id)
        if not tickets:
            telegram_helpers.send_message(
                chat_id,
                "📋 You have no tickets yet. Send me a complaint to get started!",
            )
        else:
            # Show the 5 most recent tickets
            recent = tickets[-5:]
            status_emoji = {
                "Open": "🔵",
                "Assigned": "🟣",
                "In Progress": "🟡",
                "Resolved": "🟢",
                "Reopened": "🔵",
                "Escalated": "🔴",
                "Closed": "⚫",
            }
            lines = ["📋 *Your Recent Tickets:*\n"]
            for t in reversed(recent):
                emoji = status_emoji.get(t["status"], "⚪")
                lines.append(
                    f"{emoji} `#{t['ticket_id']}` — {t['title']}\n"
                    f"   Status: *{t['status']}* | Priority: {t['priority']}"
                )
            telegram_helpers.send_message(chat_id, "\n\n".join(lines))

    else:
        telegram_helpers.send_message(
            chat_id,
            "🤔 Unknown command. Type /help to see available commands.",
        )
