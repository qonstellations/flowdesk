"""FastAPI webhook endpoint for the FlowDesk Telegram bot.

Exposes a single ``POST /webhook`` route that Telegram calls for every
incoming message.  The handler parses the update, runs the workflow,
and returns a JSON acknowledgement.
"""

from __future__ import annotations

from fastapi import FastAPI, Request

app = FastAPI(
    title="FlowDesk Telegram Webhook",
    description="Receives Telegram bot updates and processes complaints.",
)


@app.post("/webhook")
async def telegram_webhook(request: Request) -> dict:
    """Handle an incoming Telegram update.

    Parses the update payload, extracts the user's message, triggers the
    complaint-processing workflow, and returns a status dict.

    Returns
    -------
    dict
        ``{"status": "ok"}`` on success.
    """
    raise NotImplementedError("Not yet implemented")


def _parse_telegram_update(data: dict) -> tuple[str, str]:
    """Extract the Telegram chat ID and message text from a raw update.

    Parameters
    ----------
    data:
        The raw JSON body of the Telegram webhook callback.

    Returns
    -------
    tuple[str, str]
        ``(telegram_id, message_text)``

    Raises
    ------
    ValueError
        If the update does not contain a usable message.
    """
    raise NotImplementedError("Not yet implemented")
