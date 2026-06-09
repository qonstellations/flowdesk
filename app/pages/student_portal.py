import streamlit as st
from streamlit.errors import StreamlitAuthError

import backend.db as db
from backend.auth import is_allowed_email
from components.ticket_detail import render_ticket_detail
from components.ticket_table import render_ticket_table


def render() -> None:
    st.markdown('<div class="fd-section">Student Portal</div>', unsafe_allow_html=True)

    user = getattr(st, "user", None)
    is_logged_in = bool(user and getattr(user, "is_logged_in", False))

    if not is_logged_in:
        render_login_button()
        return

    email = _user_value(user, "email")
    if not email or not is_allowed_email(email):
        st.error("Use a verified Google account to view tickets.")
        if hasattr(st, "logout"):
            st.button("Sign out", on_click=st.logout)
        return

    verified_user = db.get_user_by_email(email)
    if not verified_user:
        verified_user = db.create_pending_google_user(
            email=email,
            name=_user_value(user, "name") or email,
            google_sub=_user_value(user, "sub"),
        )
        _show_link_instruction_once()

    col_email, col_logout = st.columns([3, 1])
    col_email.caption(f"Signed in as {email}")
    if hasattr(st, "logout"):
        col_logout.button("Sign out", on_click=st.logout, use_container_width=True)

    if _is_pending_google_user(verified_user):
        st.info("Talk to @flowdeskai_bot on Telegram and send /link to connect your Telegram ID to this Google account.")

    _show_ticket_list(email)


def render_login_button() -> None:
    st.caption("Sign in with Google to view tickets for your linked FlowDesk account.")
    login_error = _streamlit_login_error()
    if login_error:
        st.error(login_error)
    elif hasattr(st, "login"):
        st.button("Log in with Google", on_click=st.login, type="primary", use_container_width=True)
    else:
        st.error("This Streamlit version does not support st.login. Upgrade Streamlit to use Google login.")


def _show_ticket_list(email: str) -> None:
    tickets = db.get_tickets_by_verified_email(email)

    if not tickets:
        st.info("No tickets found for this verified account. Use Telegram /ticket to file one.")
        return

    st.caption(f"{len(tickets)} ticket(s) on record")
    render_ticket_table(tickets)

    st.markdown("---")
    st.markdown('<div class="fd-section">Ticket Detail</div>', unsafe_allow_html=True)

    ticket_options = {f"#{t['ticket_id']} — {t['title']}": t["ticket_id"] for t in tickets}
    label = st.selectbox("Select a ticket", list(ticket_options.keys()), key="student_detail")
    _show_ticket_detail(ticket_options[label])


def _show_ticket_detail(ticket_id: int) -> None:
    ticket = db.get_ticket(ticket_id)
    if not ticket:
        st.error(f"Ticket #{ticket_id} not found.")
        return
    events = db.get_events_by_ticket(ticket_id)
    render_ticket_detail(ticket, events, role="student")


def _user_value(user: object, key: str) -> str:
    value = getattr(user, key, "")
    if value:
        return str(value)
    getter = getattr(user, "get", None)
    if callable(getter):
        return str(getter(key, "") or "")
    return ""


def _is_pending_google_user(user: dict) -> bool:
    telegram_id = str(user.get("telegram_id") or "")
    return telegram_id.startswith("google:")


def _show_link_instruction_once() -> None:
    key = "flowdesk_pending_google_toast_shown"
    if st.session_state.get(key):
        return
    st.session_state[key] = True
    st.toast("Account created. Talk to @flowdeskai_bot on Telegram and use /link to connect Telegram.", icon="ℹ️")


def _streamlit_login_error() -> str:
    try:
        from streamlit.auth_util import is_authlib_installed, validate_auth_credentials
    except Exception:
        return "This Streamlit version does not expose auth helpers. Upgrade Streamlit to use Google login."

    if not is_authlib_installed():
        return "Authentication dependency missing. Run `uv sync` to install `streamlit[auth]` and Authlib."

    try:
        validate_auth_credentials("default")
    except StreamlitAuthError as exc:
        return str(exc)
    return ""
