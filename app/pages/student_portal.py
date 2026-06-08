import streamlit as st

import backend.db as db
from backend.constants import CATEGORIES, PRIORITIES
from backend.models import TicketCreate, UserCreate
from components.ticket_detail import render_ticket_detail
from components.ticket_table import render_ticket_table


def render() -> None:
    st.markdown('<div class="fd-section">Student Portal</div>', unsafe_allow_html=True)

    col_id, col_btn = st.columns([3, 1])
    with col_id:
        telegram_id = st.text_input(
            "Your Telegram ID",
            placeholder="Enter your Telegram ID to load tickets  (e.g. 123456789)",
            key="student_tid",
            label_visibility="collapsed",
        )
    with col_btn:
        search = st.button("🔍 Load Tickets", use_container_width=True, type="primary")

    if not telegram_id:
        st.markdown("""
        <div style="background:rgba(0,229,255,0.04);border:1px solid rgba(0,229,255,0.12);
                    border-radius:14px;padding:20px 24px;margin:16px 0;color:#6A748A;
                    text-align:center;font-size:0.9rem;">
            Enter your Telegram ID above to view your tickets, or use the
            <b style="color:#8A94B8;">Submit Complaint</b> tab to file a new issue.
        </div>
        """, unsafe_allow_html=True)
        tab_form, = st.tabs(["📝 Submit Complaint"])
        with tab_form:
            _show_complaint_form(telegram_id="")
        return

    tab_my, tab_new = st.tabs(["📋 My Tickets", "📝 Submit Complaint"])

    with tab_my:
        _show_ticket_list(telegram_id)

    with tab_new:
        _show_complaint_form(telegram_id)


def _show_ticket_list(telegram_id: str) -> None:
    tickets = db.get_tickets_by_telegram_id(telegram_id)

    if not tickets:
        st.info("No tickets found for this Telegram ID. Use the Submit Complaint tab to file one.")
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


def _show_complaint_form(telegram_id: str) -> None:
    st.markdown('<div class="fd-section">Submit a Complaint</div>', unsafe_allow_html=True)
    st.caption("Use this form when the Telegram bot is unavailable.")

    with st.form("complaint_form", clear_on_submit=True):
        col_n, col_t = st.columns(2)
        name = col_n.text_input("Your Name", placeholder="e.g. Rahul Sharma")
        tid = col_t.text_input(
            "Telegram ID",
            value=telegram_id,
            placeholder="e.g. 123456789",
        )

        title = st.text_input("Issue Title", placeholder="One-line summary of the problem")
        description = st.text_area("Describe the Issue", placeholder="Provide as much detail as possible — location, time, what happened.", height=110)

        col_c, col_l, col_p = st.columns(3)
        category = col_c.selectbox("Category", list(CATEGORIES))
        location = col_l.text_input("Location", placeholder="e.g. Block B, Room 204")
        priority = col_p.selectbox("Severity", list(PRIORITIES))

        submitted = st.form_submit_button("🚀 Submit Complaint", type="primary", use_container_width=True)

    if submitted:
        if not all([name.strip(), tid.strip(), title.strip(), description.strip()]):
            st.error("Please fill in Name, Telegram ID, Title, and Description.")
            return

        user = db.get_user_by_telegram_id(tid.strip())
        if not user:
            db.create_user(UserCreate(name=name.strip(), role="student", telegram_id=tid.strip()))

        ticket_id = db.create_ticket(TicketCreate(
            telegram_id=tid.strip(),
            title=title.strip(),
            description=description.strip(),
            raw_message=description.strip(),
            category=category,
            location=location.strip() or "Unknown",
            priority=priority,
        ))
        st.success(f"✅ Complaint submitted! Your ticket ID is **#{ticket_id}**. Track it under **My Tickets**.")
