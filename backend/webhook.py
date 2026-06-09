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
from fastapi.responses import HTMLResponse, JSONResponse

from backend import auth, complaint_drafts, db, telegram_helpers

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

    if db.get_active_complaint_draft(telegram_id):
        await _handle_draft_reply(message_text, telegram_id, chat_id)
    else:
        telegram_helpers.send_message(
            chat_id,
            "Use `/ticket <describe your issue>` to create a support ticket, or /help for commands.",
        )

    return JSONResponse(content={"status": "ok"})


@app.get("/auth/google/callback")
async def google_oauth_callback(code: str | None = None, state: str | None = None) -> HTMLResponse:
    if not code or not state:
        return HTMLResponse("Missing Google OAuth code or state.", status_code=400)
    try:
        link, profile = await auth.complete_google_link(code, state)
    except Exception as exc:
        return HTMLResponse(f"Could not link your account: {exc}", status_code=400)

    try:
        telegram_helpers.send_message(
            link["chat_id"],
            f"✅ Linked to verified Google account `{profile.get('email')}`. You can now use `/ticket <issue>`.",
        )
    except Exception:
        logger.exception("Failed to notify Telegram user after Google linking.")
    return HTMLResponse("FlowDesk account linked. You can return to Telegram.")


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

        db.create_user(UserCreate(name=name, role="student", telegram_id=telegram_id))
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
            f"First link your verified Google account with /link.\n"
            f"\n"
            f"*Quick start:*\n"
            f"`/ticket Wi-Fi is not working in Hostel Block A`\n"
            f"\n"
            f"Type /help for all commands, or /status to view existing tickets.",
        )
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
            "/link — Link your verified Google account\n"
            "/ticket — Create a support ticket\n"
            "/status — Check your recent tickets\n"
            "\n"
            "*Example:*\n"
            "`/ticket Wi-Fi not working in Hostel Block A`\n"
            "\n"
            "*How it works:*\n"
            "1️⃣ You describe the issue with /ticket\n"
            "2️⃣ AI validates, clarifies & routes it\n"
            "3️⃣ You get a ticket ID + target resolution\n"
            "4️⃣ Staff resolves the issue\n"
            "5️⃣ You get notified when it's done",
        )

    elif command in ("/link", "/link@flowdeskbot"):
        _ensure_user_exists(telegram_id, user_name)
        try:
            link_url = auth.create_link_url(telegram_id, chat_id, user_name)
        except Exception as exc:
            logger.exception("Could not create Google link URL.")
            telegram_helpers.send_message(
                chat_id,
                f"⚠️ Account linking is not configured correctly: {exc}",
            )
            return
        telegram_helpers.send_message(
            chat_id,
            "Open this Google sign-in link to verify your student account:\n"
            f"{link_url}\n\n"
            "The link expires in 15 minutes.",
            parse_mode=None,
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
                "Escalated": "🟠",
                "Closed": "🔴",
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

    Validates and clarifies the complaint before creating a real ticket.

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

    _ensure_user_exists(telegram_id, user_name)
    await _start_or_continue_ticket(complaint_text, telegram_id, chat_id)


async def _handle_draft_reply(message_text: str, telegram_id: str, chat_id: str) -> None:
    merged = complaint_drafts.merge_draft_answer(telegram_id, message_text)
    if not merged:
        telegram_helpers.send_message(chat_id, "That draft expired. Start again with `/ticket <issue>`.")
        return
    draft, combined = merged
    await _start_or_continue_ticket(combined, telegram_id, chat_id, answers=draft.get("answers") or [])


async def _start_or_continue_ticket(
    complaint_text: str,
    telegram_id: str,
    chat_id: str,
    answers: list[str] | None = None,
) -> None:
    user = db.get_user_by_telegram_id(telegram_id)
    if not user or not user.get("is_verified"):
        telegram_helpers.send_message(
            chat_id,
            "Please link a verified Google education account before creating tickets. Use /link to start.",
        )
        return

    telegram_helpers.send_typing_action(chat_id)
    try:
        readiness = complaint_drafts.inspect_complaint(complaint_text)
    except Exception as exc:
        logger.exception("Complaint readiness check failed.")
        telegram_helpers.send_message(
            chat_id,
            f"⚠️ I could not validate this complaint right now: {complaint_drafts.readiness_error_message(exc)}",
        )
        return

    if not readiness.is_valid:
        complaint_drafts.clear_draft(telegram_id)
        telegram_helpers.send_message(
            chat_id,
            "❌ *Ticket not created.*\n\n"
            f"{readiness.reason}\n\n"
            "Please describe a real campus issue and try again.",
        )
        return

    if not readiness.is_complete:
        questions = readiness.questions or ["What specific location or service is affected?"]
        complaint_drafts.save_draft(
            telegram_id,
            chat_id,
            readiness.complaint_text,
            readiness.missing_fields,
            questions,
            answers=answers,
        )
        telegram_helpers.send_message(
            chat_id,
            "I need a bit more detail before creating the ticket:\n"
            + "\n".join(f"- {question}" for question in questions),
        )
        return

    telegram_helpers.send_typing_action(chat_id)
    try:
        from backend.workflow import run_workflow

        final_state = run_workflow(readiness.complaint_text, telegram_id)
    except Exception as exc:
        logger.exception("Workflow failed for telegram_id=%s", telegram_id)
        telegram_helpers.send_message(
            chat_id,
            f"⚠️ Sorry, I could not create the ticket: {exc}",
        )
        return

    complaint_drafts.clear_draft(telegram_id)
    reply = telegram_helpers.format_ticket_reply(
        ticket_id=final_state["ticket_id"],
        department=final_state.get("assigned_dept"),
        priority=final_state.get("priority") or "Medium",
        target_resolution_at=final_state.get("target_resolution_at") or "TBD",
    )
    telegram_helpers.send_message(chat_id, reply)

    logger.info("Ticket #%s created for telegram_id=%s", final_state["ticket_id"], telegram_id)
