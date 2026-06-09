"""Google OAuth helpers for Telegram linking and portal verification."""

from __future__ import annotations

import os
import secrets
from urllib.parse import urlencode

import httpx

from backend import db


GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


def allowed_email_domains() -> list[str]:
    raw = os.getenv("ALLOWED_EMAIL_DOMAINS", "")
    return [part.strip().lower() for part in raw.split(",") if part.strip()]


def is_allowed_email(email: str) -> bool:
    if not email.strip():
        return False
    domains = allowed_email_domains()
    if not domains:
        return True
    normalized = email.strip().lower()
    for domain in domains:
        if domain.startswith(".") and normalized.endswith(domain):
            return True
        if normalized.endswith("@" + domain.lstrip("@")):
            return True
    return False


def create_link_url(telegram_id: str, chat_id: str, user_name: str) -> str:
    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "").strip()
    if not client_id or not redirect_uri:
        raise RuntimeError("GOOGLE_CLIENT_ID and GOOGLE_REDIRECT_URI are required for /link.")

    token = secrets.token_urlsafe(32)
    db.create_link_token(token, telegram_id, chat_id, user_name)
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": token,
        "prompt": "select_account",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def complete_google_link(code: str, state: str) -> tuple[dict, dict]:
    link = db.consume_link_token(state)
    if not link:
        raise ValueError("This link request is invalid or has expired. Start again with /link.")

    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "").strip()
    if not client_id or not client_secret or not redirect_uri:
        raise RuntimeError("Google OAuth is not fully configured.")

    async with httpx.AsyncClient(timeout=20.0) as client:
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        token_response.raise_for_status()
        access_token = token_response.json()["access_token"]

        userinfo_response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        userinfo_response.raise_for_status()
        profile = userinfo_response.json()

    email = profile.get("email", "")
    if not profile.get("email_verified") or not email:
        raise ValueError("Please use a verified Google account with a confirmed email address.")

    db.link_verified_user(
        telegram_id=link["telegram_id"],
        name=profile.get("name") or link["user_name"],
        email=email,
        google_sub=profile.get("sub", ""),
    )
    return link, profile
