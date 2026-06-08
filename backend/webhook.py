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
from backend.complaint_validation import validate_complaint_text

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

    # ── Natural language fallback — redirect to /ticket or /help ──
    telegram_helpers.send_message(
        chat_id,
        "💬 Hey! I'm not able to process free-text messages directly.\n"
        "\n"
        "To create a support ticket, use:\n"
        "`/ticket <describe your issue>`\n"
        "\n"
        "For example:\n"
        "• `/ticket Wi-Fi not working in Hostel Block A`\n"
        "• `/ticket Water leakage in Room 204`\n"
        "\n"
        "Type /help to see all available commands.",
    )

    return JSONResponse(content={"status": "ok"})


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
            f"I'm your campus complaint assistant. Use the /ticket command "
            f"to raise a support ticket.\n"
            f"\n"
            f"*Quick start:*\n"
            f"`/ticket Wi-Fi is not working in Hostel Block A`\n"
            f"`/ticket Water leakage in Room 204`\n"
            f"`/ticket Mess food quality has been poor this week`\n"
            f"\n"
            f"Type /help for all commands.",
        )
        # Auto-register on /start
        _ensure_user_exists(telegram_id, user_name)

    elif command in ("/help", "/help@flowdeskbot"):
        telegram_helpers.send_message(
            chat_id,
            "ℹ️ *FlowDesk Help*\n"
            "\n"
            "Use `/ticket` followed by your complaint to raise a support ticket.\n"
            "\n"
            "*Commands:*\n"
            "/start — Welcome message\n"
            "/help — This help text\n"
            "/ticket — Create a support ticket\n"
            "/status — Check your recent tickets\n"
            "\n"
            "*Example:*\n"
            "`/ticket Wi-Fi not working in Hostel Block A`\n"
            "\n"
            "*How it works:*\n"
            "1️⃣ You describe the issue with /ticket\n"
            "2️⃣ AI validates, classifies & routes it\n"
            "3️⃣ You get a ticket ID + SLA deadline\n"
            "4️⃣ Staff resolves the issue\n"
            "5️⃣ You get notified when it's done",
        )

    elif command in ("/status", "/status@flowdeskbot"):
        tickets = db.get_tickets_by_telegram_id(telegram_id)
        if not tickets:
            telegram_helpers.send_message(
                chat_id,
                "📋 You have no tickets yet. Use `/ticket <your issue>` to create one!",
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

    elif command in ("/ticket", "/ticket@flowdeskbot"):
        await _handle_ticket_command(message_text, telegram_id, chat_id, user_name)

    else:
        telegram_helpers.send_message(
            chat_id,
            "🤔 Unknown command. Type /help to see available commands.",
        )


async def _handle_ticket_command(
    message_text: str,
    telegram_id: str,
    chat_id: str,
    user_name: str,
) -> None:
    """Handle the ``/ticket <description>`` command.

    Validates the complaint before creating a real ticket through the
    workflow.

    Parameters
    ----------
    message_text:
        The full message text (starts with ``/ticket``).
    telegram_id:
        The sender's Telegram user ID.
    chat_id:
        The chat to reply to.
    user_name:
        The sender's display name.
    """
    # Extract the complaint text after "/ticket"
    parts = message_text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        telegram_helpers.send_message(
            chat_id,
            "📝 Please describe your issue after the /ticket command.\n"
            "\n"
            "*Usage:* `/ticket <describe your issue>`\n"
            "\n"
            "*Examples:*\n"
            "• `/ticket Wi-Fi not working in Hostel Block A`\n"
            "• `/ticket Water leakage in Room 204`",
        )
        return

    complaint_text = parts[1].strip()

    validation = validate_complaint_text(complaint_text)
    if not validation.is_valid:
        telegram_helpers.send_message(
            chat_id,
            "❌ *Ticket not created.*\n"
            "\n"
            f"{validation.rejection_reason}\n"
            "\n"
            "Please describe a real campus issue and try again.\n"
            "*Example:* `/ticket Wi-Fi not working in Hostel Block A`",
        )
        logger.info(
            "Ticket rejected by deterministic validation for telegram_id=%s — reason: %s",
            telegram_id,
            validation.rejection_reason,
        )
        return

    # ── Show typing indicator while validating ──
    telegram_helpers.send_typing_action(chat_id)

    # ── LLM validation gate ──
    from backend.llm import call_gemini

    validation_prompt = f"""You are a ticket validation agent for a university campus helpdesk called FlowDesk.
Your job is to decide whether a student's message is a LEGITIMATE campus complaint that deserves a support ticket.

REJECT the message (is_valid = false) if it is:
- Random gibberish, keyboard mashing, or test messages (e.g. "asdfgh", "test", "hello", "123")
- Greetings or casual chat (e.g. "hi", "what's up", "how are you")
- Jokes, memes, or trolling
- Completely empty or meaningless content
- Not related to a campus facility, service, or academic issue at all
- Abusive spam with no real complaint

ACCEPT the message (is_valid = true) if it describes any real issue, even if vaguely, related to:
- Infrastructure (Wi-Fi, electricity, water, maintenance)
- Hostel or campus facilities
- Mess or food quality
- Academics (grades, exams, scheduling)
- Any genuine campus concern

Be lenient with grammar and spelling — students may type quickly. Focus on whether there is a REAL issue being described.

Student message:
"{complaint_text}"
"""

    validation_schema = {
        "type": "OBJECT",
        "properties": {
            "is_valid": {
                "type": "BOOLEAN",
                "description": "true if this is a legitimate campus complaint, false if garbage/spam/irrelevant"
            },
            "rejection_reason": {
                "type": "STRING",
                "description": "A brief, friendly explanation of why the ticket was rejected (only used when is_valid is false)"
            }
        },
        "required": ["is_valid", "rejection_reason"]
    }

    try:
        result = call_gemini(validation_prompt, response_schema=validation_schema)
        is_valid = result.get("is_valid", True)
        rejection_reason = result.get("rejection_reason", "")
    except Exception:
        # If validation fails, err on the side of accepting
        logger.warning("Ticket validation LLM call failed — accepting by default.")
        is_valid = True
        rejection_reason = ""

    if not is_valid:
        telegram_helpers.send_message(
            chat_id,
            "❌ *Ticket not created.*\n"
            "\n"
            f"{rejection_reason}\n"
            "\n"
            "Please describe a real campus issue and try again.\n"
            "*Example:* `/ticket Wi-Fi not working in Hostel Block A`",
        )
        logger.info(
            "Ticket rejected for telegram_id=%s — reason: %s",
            telegram_id,
            rejection_reason,
        )
        return

    # ── Complaint is valid — auto-register and run the workflow ──
    _ensure_user_exists(telegram_id, user_name)

    telegram_helpers.send_typing_action(chat_id)

    try:
        from backend.workflow import run_workflow

        final_state = run_workflow(
            raw_message=complaint_text,
            telegram_id=telegram_id,
        )
    except Exception as exc:
        logger.exception("Workflow failed for telegram_id=%s", telegram_id)
        telegram_helpers.send_message(
            chat_id,
            "⚠️ Sorry, something went wrong processing your complaint. "
            "Please try again or contact the admin directly.",
        )
        return

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
