import streamlit as st
import streamlit.components.v1 as _components
from streamlit.errors import StreamlitAuthError

import backend.db as db
from backend.auth import is_allowed_email
from backend.models import TicketCreate
from components.ticket_detail import render_ticket_detail
from components.ticket_table import render_ticket_table

# ── Hero HTML (self-contained iframe — no Streamlit CSS bleeds in) ─────────

_HERO_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap');

*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html,body{background:#050C1A;font-family:'Space Grotesk',sans-serif;color:#E0E6F4;overflow:hidden}
body{padding:28px 32px 16px}

/* ── INTRO keyframes ─────────────────────────────── */
@keyframes fd-up{
  from{opacity:0;transform:translateY(14px)}
  to  {opacity:1;transform:translateY(0)}
}
@keyframes fd-draw{
  from{width:0}
  to  {width:calc(100% - 18px)}
}
@keyframes fd-pop{
  0%  {transform:scale(.3);opacity:0}
  65% {transform:scale(1.18)}
  100%{transform:scale(1);opacity:1}
}

/* ── LOOP keyframes (12 s, starts at 3.6 s) ────── */
/* Spine fill: start full (continuation), quick reset, advance 4 stages */
@keyframes fd-sfill{
  0%,3%  {width:calc(100% - 18px);opacity:1}
  5%,6%  {width:0;opacity:.3}
  8%,30% {width:0;opacity:1}
  32%,53%{width:33.3%}
  55%,76%{width:66.6%}
  78%,100%{width:calc(100% - 18px)}
}

/* Node 1 — cyan, lit for entire loop except reset dip */
@keyframes fd-n1{
  0%,3%  {background:#00E5FF;box-shadow:0 0 0 3px rgba(0,229,255,.3),0 0 18px rgba(0,229,255,.55)}
  4%,7%  {background:rgba(0,229,255,.12);box-shadow:0 0 0 2px rgba(0,229,255,.12)}
  8%,100%{background:#00E5FF;box-shadow:0 0 0 3px rgba(0,229,255,.3),0 0 18px rgba(0,229,255,.55)}
}
/* Node 2 — amber, off stage 1 */
@keyframes fd-n2{
  0%,3%  {background:#FFB347;box-shadow:0 0 0 3px rgba(255,179,71,.3),0 0 18px rgba(255,179,71,.5)}
  4%,30% {background:rgba(255,179,71,.1);box-shadow:0 0 0 2px rgba(255,179,71,.12)}
  32%,100%{background:#FFB347;box-shadow:0 0 0 3px rgba(255,179,71,.3),0 0 18px rgba(255,179,71,.5)}
}
/* Node 3 — orange, off stages 1-2 */
@keyframes fd-n3{
  0%,3%  {background:#FF8C00;box-shadow:0 0 0 3px rgba(255,140,0,.3),0 0 18px rgba(255,140,0,.5)}
  4%,53% {background:rgba(255,140,0,.1);box-shadow:0 0 0 2px rgba(255,140,0,.12)}
  55%,100%{background:#FF8C00;box-shadow:0 0 0 3px rgba(255,140,0,.3),0 0 18px rgba(255,140,0,.5)}
}
/* Node 4 — green, off stages 1-3 */
@keyframes fd-n4{
  0%,3%  {background:#4CD97B;box-shadow:0 0 0 3px rgba(76,217,123,.35),0 0 22px rgba(76,217,123,.65)}
  4%,76% {background:rgba(76,217,123,.1);box-shadow:0 0 0 2px rgba(76,217,123,.14)}
  78%,100%{background:#4CD97B;box-shadow:0 0 0 3px rgba(76,217,123,.35),0 0 22px rgba(76,217,123,.65)}
}

/* Beat active-dim cycling */
@keyframes fd-b1{0%,7%{opacity:.55}8%,30%{opacity:1}32%,100%{opacity:.55}}
@keyframes fd-b2{0%,30%{opacity:.55}32%,53%{opacity:1}55%,100%{opacity:.55}}
@keyframes fd-b3{0%,53%{opacity:.55}55%,76%{opacity:1}78%,100%{opacity:.55}}
@keyframes fd-b4{0%,76%{opacity:.55}78%,100%{opacity:1}}

/* Status line hide/show per stage */
@keyframes fd-s1{0%,7%{opacity:0}8%,30%{opacity:1}32%,100%{opacity:0}}
@keyframes fd-s2{0%,30%{opacity:0}32%,53%{opacity:1}55%,100%{opacity:0}}
@keyframes fd-s3{0%,53%{opacity:0}55%,76%{opacity:1}78%,100%{opacity:0}}
@keyframes fd-s4{0%,76%{opacity:0}78%,100%{opacity:1}}

/* ── LAYOUT ──────────────────────────────────────── */
.wordmark{
  display:flex;justify-content:space-between;align-items:flex-start;
  margin-bottom:28px;
  animation:fd-up .5s ease-out .1s both
}
.wm-name{font-size:1.55rem;font-weight:900;letter-spacing:-.04em;color:#00E5FF;line-height:1}
.wm-tag{font-size:.65rem;letter-spacing:.14em;text-transform:uppercase;color:#4A5470;margin-top:4px}
.sys-status{display:flex;align-items:center;gap:6px;font-size:.72rem;color:#4A5470;margin-top:4px}
.sys-dot{width:7px;height:7px;border-radius:50%;background:#4CD97B;box-shadow:0 0 8px rgba(76,217,123,.6);flex-shrink:0}

/* Four beats */
.beats{display:grid;grid-template-columns:repeat(4,1fr);gap:0;margin-bottom:24px}
.beat{padding:0 12px 0 0}
.beat:last-child{padding-right:0}
.beat-num{font-size:.6rem;letter-spacing:.18em;text-transform:uppercase;font-weight:700;margin-bottom:5px}
.beat-hl{font-size:.88rem;font-weight:700;color:#C8D0E8;line-height:1.35;margin-bottom:6px;letter-spacing:-.01em}
.beat-tag{display:inline-block;font-size:.6rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;padding:2px 7px;border-radius:20px;border:1px solid currentColor;opacity:.75}

.beat-1 .beat-num{color:rgba(0,229,255,.55)} .beat-1 .beat-tag{color:#00E5FF}
.beat-2 .beat-num{color:rgba(255,179,71,.55)}.beat-2 .beat-tag{color:#FFB347}
.beat-3 .beat-num{color:rgba(255,140,0,.55)} .beat-3 .beat-tag{color:#FF8C00}
.beat-4 .beat-num{color:rgba(76,217,123,.55)}.beat-4 .beat-tag{color:#4CD97B}

/* Staggered intro + loop active cycling */
.beat-1{animation:fd-up .45s ease-out .3s both, fd-b1 12s ease-in-out 3.6s infinite}
.beat-2{animation:fd-up .45s ease-out .55s both,fd-b2 12s ease-in-out 3.6s infinite}
.beat-3{animation:fd-up .45s ease-out .8s both, fd-b3 12s ease-in-out 3.6s infinite}
.beat-4{animation:fd-up .45s ease-out 1.05s both,fd-b4 12s ease-in-out 3.6s infinite}

/* ── SPINE ───────────────────────────────────────── */
.spine-wrap{animation:fd-up .4s ease-out 1.45s both;margin-bottom:14px}
.spine-track{position:relative;height:52px}

/* Base (unlit) line */
.spine-base{
  position:absolute;top:16px;left:9px;right:9px;height:1.5px;
  background:rgba(0,229,255,.08);border-radius:2px
}
/* Animated fill */
.spine-fill{
  position:absolute;top:16px;left:9px;height:1.5px;width:0;
  background:linear-gradient(90deg,#00E5FF 0%,#FFB347 33%,#FF8C00 66%,#4CD97B 100%);
  border-radius:2px;
  animation:
    fd-draw .8s cubic-bezier(.4,0,.2,1) 1.7s both,
    fd-sfill 12s ease-in-out 3.6s infinite
}
/* Node row */
.spine-nodes{
  position:absolute;top:7px;left:0;right:0;
  display:flex;justify-content:space-between
}
.node{
  width:18px;height:18px;border-radius:50%;border:2px solid;
  position:relative;flex-shrink:0
}
.node-lbl{
  position:absolute;top:22px;left:50%;transform:translateX(-50%);
  font-size:.56rem;letter-spacing:.1em;text-transform:uppercase;
  white-space:nowrap;font-weight:700;color:#4A5470
}
/* Node intro pops + loop glows */
.n1{border-color:rgba(0,229,255,.35);background:rgba(0,229,255,.1);
    animation:fd-pop .4s cubic-bezier(.34,1.56,.64,1) 2.0s both,fd-n1 12s ease-in-out 3.6s infinite}
.n2{border-color:rgba(255,179,71,.35);background:rgba(255,179,71,.1);
    animation:fd-pop .4s cubic-bezier(.34,1.56,.64,1) 2.3s both,fd-n2 12s ease-in-out 3.6s infinite}
.n3{border-color:rgba(255,140,0,.35);background:rgba(255,140,0,.1);
    animation:fd-pop .4s cubic-bezier(.34,1.56,.64,1) 2.6s both,fd-n3 12s ease-in-out 3.6s infinite}
.n4{border-color:rgba(76,217,123,.35);background:rgba(76,217,123,.1);
    animation:fd-pop .4s cubic-bezier(.34,1.56,.64,1) 2.9s both,fd-n4 12s ease-in-out 3.6s infinite}

/* ── STATUS LINE ─────────────────────────────────── */
.status-bar{
  position:relative;height:20px;
  animation:fd-up .35s ease-out 3.1s both
}
.smsg{
  position:absolute;left:0;
  font-family:'JetBrains Mono','Courier New',monospace;
  font-size:.7rem;font-weight:500;letter-spacing:.04em;
  color:rgba(0,229,255,.72);opacity:0;white-space:nowrap
}
.smsg.s4{color:rgba(76,217,123,.8)}

/* s1 visible on page load (backwards fills 0% keyframe = opacity 0, then loop starts)
   use a tiny intro-only anim to show it before loop */
.s1-init{
  position:absolute;left:0;
  font-family:'JetBrains Mono','Courier New',monospace;
  font-size:.7rem;font-weight:500;letter-spacing:.04em;
  color:rgba(0,229,255,.72);white-space:nowrap;
  animation:fd-up .35s ease-out 3.1s both
}

.smsg.s1{animation:fd-s1 12s ease-in-out 3.6s infinite}
.smsg.s2{animation:fd-s2 12s ease-in-out 3.6s infinite}
.smsg.s3{animation:fd-s3 12s ease-in-out 3.6s infinite}
.smsg.s4{animation:fd-s4 12s ease-in-out 3.6s infinite}

/* ── REDUCED MOTION ──────────────────────────────── */
@media(prefers-reduced-motion:reduce){
  .wordmark,.beat-1,.beat-2,.beat-3,.beat-4,.spine-wrap,.status-bar,.s1-init{
    animation:none!important;opacity:1!important;transform:none!important
  }
  .spine-fill{animation:none!important;width:calc(100% - 18px)!important}
  .n1{animation:none!important;background:#00E5FF!important;box-shadow:0 0 0 3px rgba(0,229,255,.3),0 0 18px rgba(0,229,255,.55)!important}
  .n2{animation:none!important;background:#FFB347!important;box-shadow:0 0 0 3px rgba(255,179,71,.3),0 0 18px rgba(255,179,71,.5)!important}
  .n3{animation:none!important;background:#FF8C00!important;box-shadow:0 0 0 3px rgba(255,140,0,.3),0 0 18px rgba(255,140,0,.5)!important}
  .n4{animation:none!important;background:#4CD97B!important;box-shadow:0 0 0 3px rgba(76,217,123,.35),0 0 22px rgba(76,217,123,.65)!important}
  .s1-init{display:none!important}
  .smsg.s4{animation:none!important;opacity:1!important}
}

/* Keyboard focus */
a:focus-visible,button:focus-visible{outline:2px solid #00E5FF;outline-offset:3px;border-radius:4px}
</style>
</head>
<body>

<!-- Wordmark row -->
<div class="wordmark">
  <div>
    <div class="wm-name">FlowDesk</div>
    <div class="wm-tag">Autonomous Campus Issue Resolution</div>
  </div>
  <div class="sys-status">
    <div class="sys-dot"></div>
    All systems online
  </div>
</div>

<!-- Four narrative beats -->
<div class="beats">
  <div class="beat beat-1">
    <div class="beat-num">01</div>
    <div class="beat-hl">Spotted a problem on campus?</div>
    <span class="beat-tag">Raised</span>
  </div>
  <div class="beat beat-2">
    <div class="beat-num">02</div>
    <div class="beat-hl">Our AI routes it to the right desk.</div>
    <span class="beat-tag">Classified by AI</span>
  </div>
  <div class="beat beat-3">
    <div class="beat-num">03</div>
    <div class="beat-hl">The right team picks it up.</div>
    <span class="beat-tag">Assigned</span>
  </div>
  <div class="beat beat-4">
    <div class="beat-num">04</div>
    <div class="beat-hl">Track it till it's fixed.</div>
    <span class="beat-tag">Resolved</span>
  </div>
</div>

<!-- Spine -->
<div class="spine-wrap">
  <div class="spine-track">
    <div class="spine-base"></div>
    <div class="spine-fill"></div>
    <div class="spine-nodes">
      <div class="node n1"><span class="node-lbl">Raised</span></div>
      <div class="node n2"><span class="node-lbl">AI</span></div>
      <div class="node n3"><span class="node-lbl">Assigned</span></div>
      <div class="node n4"><span class="node-lbl">Resolved</span></div>
    </div>
  </div>
</div>

<!-- Status line -->
<div class="status-bar">
  <!-- Shown only during intro window before loop takes over -->
  <span class="s1-init">&#9679; Complaint received &middot; Routing in progress&hellip;</span>
  <!-- Loop-driven messages -->
  <span class="smsg s1">&#9679; Complaint received &middot; Routing in progress&hellip;</span>
  <span class="smsg s2">&#9679; Routing to IT Department&hellip;</span>
  <span class="smsg s3">&#9679; Assigned to Hostel Admin</span>
  <span class="smsg s4">&#10003; Resolved &middot; 4 hr 22 min</span>
</div>

</body>
</html>"""


def render_hero() -> None:
    """Full-width animated hero shown on the student login page."""
    _components.html(_HERO_HTML, height=310, scrolling=False)

    login_error = _streamlit_login_error()
    if login_error:
        st.error(login_error)
        return
    _, btn_col, _ = st.columns([1, 2, 1])
    with btn_col:
        if hasattr(st, "login"):
            st.button(
                "Sign in with Google →",
                on_click=st.login,
                type="primary",
                use_container_width=True,
                key="hero_login_btn",
            )
        else:
            st.error("Upgrade Streamlit to use Google login.")


def render() -> None:
    st.html('<div class="fd-section">Student Portal</div>')

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

    tab_submit, tab_tickets = st.tabs(["Submit Ticket", "My Tickets"])
    with tab_submit:
        _render_submit_form(verified_user)
    with tab_tickets:
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


def _render_submit_form(verified_user: dict) -> None:
    st.html('<div class="fd-section">New Ticket</div>')

    result = st.session_state.pop("_ticket_submit_result", None)
    if result:
        if result.get("ok"):
            st.success(f"Ticket #{result['ticket_id']} submitted. Use /status on Telegram or check My Tickets to track it.")
        else:
            st.error(result.get("error", "Something went wrong."))

    with st.form("submit_ticket_form", clear_on_submit=True):
        category = st.selectbox(
            "Category",
            ["IT & Wi-Fi", "Hostel Maintenance", "Campus Maintenance", "Mess & Food", "Academics", "Other"],
        )
        title = st.text_input("Title", placeholder="Short summary of your issue", max_chars=120)
        description = st.text_area("Description", placeholder="Describe the issue in detail", height=130)
        urgency = st.selectbox("Urgency", ["Low", "Medium", "High"])
        submitted = st.form_submit_button("Submit Ticket →", type="primary", use_container_width=True)

    if submitted:
        if not title.strip():
            st.session_state["_ticket_submit_result"] = {"ok": False, "error": "Title is required."}
            st.rerun()
        elif not description.strip():
            st.session_state["_ticket_submit_result"] = {"ok": False, "error": "Description is required."}
            st.rerun()
        else:
            try:
                ticket_id = db.create_ticket(TicketCreate(
                    telegram_id=verified_user["telegram_id"],
                    title=title.strip(),
                    description=description.strip(),
                    raw_message=description.strip(),
                    category=category,
                    priority=urgency,
                ))
                st.session_state["_ticket_submit_result"] = {"ok": True, "ticket_id": ticket_id}
            except Exception as exc:
                st.session_state["_ticket_submit_result"] = {"ok": False, "error": str(exc)}
            st.rerun()


def _show_ticket_list(email: str) -> None:
    tickets = db.get_tickets_by_verified_email(email)

    if not tickets:
        st.info("No tickets yet. Use the Submit Ticket tab or Telegram /ticket to file one.")
        return

    st.caption(f"{len(tickets)} ticket(s) on record")
    render_ticket_table(tickets)

    st.markdown("---")
    st.html('<div class="fd-section">Ticket Detail</div>')

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
