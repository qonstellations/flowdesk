"""Webhook command handling tests."""

import asyncio

import pytest

from backend import webhook


def test_ticket_command_rejects_garbage_before_workflow(monkeypatch: pytest.MonkeyPatch) -> None:
    sent_messages: list[tuple[str, str]] = []
    typing_calls: list[str] = []
    ensured_users: list[tuple[str, str]] = []

    monkeypatch.setattr(
        webhook.telegram_helpers,
        "send_message",
        lambda chat_id, message: sent_messages.append((chat_id, message)),
    )
    monkeypatch.setattr(
        webhook.telegram_helpers,
        "send_typing_action",
        lambda chat_id: typing_calls.append(chat_id),
    )
    monkeypatch.setattr(
        webhook,
        "_ensure_user_exists",
        lambda telegram_id, name: ensured_users.append((telegram_id, name)),
    )

    asyncio.run(
        webhook._handle_ticket_command(
            "/ticket boogie boogie pookie pookie",
            telegram_id="123",
            chat_id="456",
            user_name="Test User",
        )
    )

    assert sent_messages
    assert sent_messages[0][0] == "456"
    assert "Ticket not created" in sent_messages[0][1]
    assert typing_calls == []
    assert ensured_users == []
