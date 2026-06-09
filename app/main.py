import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

import backend.db as db

st.set_page_config(
    page_title="FlowDesk",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700;800;900&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Space Grotesk', sans-serif !important;
}
.stApp {
    background: #070C18;
    background-image:
        radial-gradient(ellipse 60% 40% at 15% 60%, rgba(0,229,255,0.055) 0%, transparent 70%),
        radial-gradient(ellipse 50% 50% at 85% 15%, rgba(124,77,255,0.07) 0%, transparent 70%);
    color: #E0E6F4;
}

/* ── Hide sidebar entirely ─────────────────────────── */
section[data-testid="stSidebar"]          { display: none !important; }
button[data-testid="collapsedControl"]    { display: none !important; }
[data-testid="stDecoration"]              { display: none !important; }

/* ── Top navbar ────────────────────────────────────── */
.fd-navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 32px;
    background: rgba(12, 18, 34, 0.88);
    border-bottom: 1px solid rgba(0,229,255,0.1);
    backdrop-filter: blur(16px);
    border-radius: 0 0 18px 18px;
    margin-bottom: 0;
}
.fd-logo {
    font-size: 1.85rem;
    font-weight: 900;
    letter-spacing: -0.04em;
    color: #00E5FF;
    line-height: 1.05;
}
.fd-brand {
    display: flex;
    align-items: center;
    gap: 14px;
}
.fd-brand-icon {
    flex-shrink: 0;
    opacity: 0.92;
}
.fd-tagline {
    font-size: 0.72rem;
    color: #4A5470;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-top: 2px;
}
.fd-status {
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: 0.8rem;
    color: #4A5470;
}
.fd-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #4CD97B;
    box-shadow: 0 0 10px #4CD97B80;
    flex-shrink: 0;
}

/* ── Landing hero ──────────────────────────────────── */
.fd-hero {
    text-align: center;
    padding: 5rem 2rem 2.5rem;
}
.fd-hero-title {
    font-size: clamp(5rem, 14vw, 11rem);
    font-weight: 900;
    letter-spacing: -0.06em;
    line-height: 0.95;
    color: #E0E6F4;
    margin-bottom: 1.5rem;
}
.fd-hero-sub {
    font-size: 1rem;
    color: rgba(224,230,244,0.62);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-weight: 400;
    margin-bottom: 0.5rem;
}
.fd-hero-divider {
    width: 60px;
    height: 2px;
    background: #00E5FF;
    margin: 1.2rem auto 3rem;
    border-radius: 2px;
}

/* ── Role cards ────────────────────────────────────── */
.role-card {
    background: linear-gradient(155deg, rgba(14,22,48,0.96) 0%, rgba(10,16,34,0.99) 100%);
    border-radius: 22px;
    padding: 2.5rem 2rem 2rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: transform 0.25s ease, border-color 0.25s ease;
    box-shadow: 0 4px 30px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.04);
    height: 100%;
}
.role-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
}
.role-card-student { border: 1px solid rgba(0,229,255,0.2); }
.role-card-student::before { background: linear-gradient(90deg, transparent, #00E5FF, transparent); }
.role-card-admin   { border: 1px solid rgba(255,165,0,0.2); }
.role-card-admin::before   { background: linear-gradient(90deg, transparent, #FFA500, transparent); }

.role-card:hover { transform: translateY(-6px); box-shadow: 0 14px 48px rgba(0,0,0,0.5); }
.role-card-student:hover { border-color: rgba(0,229,255,0.5); }
.role-card-admin:hover   { border-color: rgba(255,165,0,0.5); }

.role-icon  { margin-bottom: 1rem; display: flex; justify-content: center; }
.role-title { font-size: 1.5rem; font-weight: 800; margin-bottom: 0.5rem; letter-spacing: -0.02em; }
.role-title-student { color: #00E5FF; }
.role-title-admin   { color: #FFA500; }
.role-desc  { font-size: 0.88rem; color: rgba(224,230,244,0.45); line-height: 1.6; margin-bottom: 1.8rem; }

/* ── Login panel ───────────────────────────────────── */
.login-header {
    text-align: center;
    padding: 2.5rem 0 1.5rem;
}
.login-title {
    font-size: 2rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    margin-bottom: 0.4rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
}
.login-back {
    font-size: 0.82rem;
    color: #4A5470;
    cursor: pointer;
    letter-spacing: 0.05em;
}

/* ── Metric cards ──────────────────────────────────── */
.metric-card {
    background: linear-gradient(155deg, rgba(18,26,50,0.95) 0%, rgba(12,18,36,0.98) 100%);
    border: 1px solid rgba(0,229,255,0.14);
    border-radius: 18px;
    padding: 26px 18px 22px;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: all 0.25s ease;
    box-shadow: 0 2px 20px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.04);
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(0,229,255,0.4), transparent);
}
.metric-card:hover {
    transform: translateY(-5px);
    border-color: rgba(0,229,255,0.3);
    box-shadow: 0 8px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.06);
}
.metric-value {
    font-size: 2.8rem;
    font-weight: 700;
    line-height: 1;
    letter-spacing: -0.02em;
}
.metric-label {
    font-size: 0.72rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #5A6480;
    margin-top: 8px;
    font-weight: 500;
}

/* ── Section headings ──────────────────────────────── */
.fd-section {
    font-size: 1.25rem;
    font-weight: 700;
    color: #C8D0E8;
    margin: 20px 0 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(0,229,255,0.08);
    letter-spacing: -0.01em;
}

/* ── Streamlit pills (nav) ─────────────────────────── */
[data-testid="stButtonGroup"] {
    gap: 12px !important;
    justify-content: center !important;
}
[data-testid="stBaseButton-pills"] {
    background: rgba(16,24,50,0.9) !important;
    border: 1.5px solid rgba(0,229,255,0.28) !important;
    border-radius: 14px !important;
    color: #9AAAC8 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
    padding: 14px 40px !important;
    letter-spacing: 0.03em !important;
    transition: all 0.2s ease !important;
    min-width: 200px !important;
}
[data-testid="stBaseButton-pills"]:hover {
    background: rgba(0,229,255,0.1) !important;
    border-color: rgba(0,229,255,0.6) !important;
    color: #00E5FF !important;
    transform: translateY(-2px) !important;
}
[data-testid="stBaseButton-pillsActive"] {
    background: rgba(0,229,255,0.12) !important;
    border: 1.5px solid #00E5FF !important;
    border-radius: 14px !important;
    color: #00E5FF !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
    padding: 14px 40px !important;
    letter-spacing: 0.03em !important;
    min-width: 200px !important;
    transition: all 0.2s ease !important;
}

/* ── Streamlit buttons ─────────────────────────────── */
div[data-testid="stButton"] > button {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.01em !important;
}
div[data-testid="stButton"] > button:hover {
    transform: translateY(-2px) !important;
}
div[data-testid="stButton"] > button[kind="primary"] {
    background: #00C4E0 !important;
    border: none !important;
    color: #070C18 !important;
}

/* ── Tabs ──────────────────────────────────────────── */
div[data-testid="stTabs"] > div > div > button {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    letter-spacing: 0.02em !important;
    color: #6A748A !important;
    border-radius: 8px 8px 0 0 !important;
}
div[data-testid="stTabs"] > div > div > button[aria-selected="true"] {
    color: #00E5FF !important;
}

/* ── Divider ───────────────────────────────────────── */
hr {
    border: none !important;
    border-top: 1px solid rgba(0,229,255,0.08) !important;
    margin: 20px 0 !important;
}

/* ── Inputs / selects ──────────────────────────────── */
div[data-testid="stSelectbox"] label,
div[data-testid="stTextInput"] label,
div[data-testid="stTextArea"] label {
    font-weight: 600 !important;
    color: #8A94B8 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
}

/* ── Landing headline ──────────────────────────────── */
.fd-headline {
    font-size: clamp(1.1rem, 2.5vw, 1.75rem);
    font-weight: 400;
    color: rgba(224,230,244,0.78);
    letter-spacing: -0.01em;
    line-height: 1.5;
    margin-bottom: 2rem;
}
.fd-strike {
    position: relative;
    display: inline-block;
    white-space: nowrap;
    color: rgba(224,230,244,0.38);
}
.fd-strike-svg {
    position: absolute;
    left: -4px;
    top: 0;
    width: calc(100% + 8px);
    height: 100%;
    overflow: visible;
    pointer-events: none;
}

/* ── Background pipeline animation ────────────────── */
@keyframes fd-flow {
    from { stroke-dashoffset: 72; }
    to   { stroke-dashoffset: 0; }
}
</style>
""", unsafe_allow_html=True)

db.init_db()

st.markdown("""
<div style="position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;pointer-events:none;overflow:hidden">
<svg width="100%" height="100%" viewBox="0 0 1440 800" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
  <!-- Static structure -->
  <line x1="220" y1="400" x2="314" y2="400" stroke="rgba(0,229,255,0.05)" stroke-width="1.2"/>
  <line x1="364" y1="400" x2="502" y2="400" stroke="rgba(0,229,255,0.05)" stroke-width="1.2"/>
  <path d="M 526,388 Q 600,290 716,290" stroke="rgba(0,229,255,0.05)" stroke-width="1.2" fill="none"/>
  <line x1="526" y1="400" x2="716" y2="400" stroke="rgba(0,229,255,0.05)" stroke-width="1.2"/>
  <path d="M 526,412 Q 600,510 716,510" stroke="rgba(0,229,255,0.05)" stroke-width="1.2" fill="none"/>
  <path d="M 740,290 Q 840,290 888,374" stroke="rgba(0,229,255,0.05)" stroke-width="1.2" fill="none"/>
  <line x1="740" y1="400" x2="888" y2="400" stroke="rgba(0,229,255,0.05)" stroke-width="1.2"/>
  <path d="M 740,510 Q 840,510 888,426" stroke="rgba(0,229,255,0.05)" stroke-width="1.2" fill="none"/>
  <!-- Animated flow dashes -->
  <line x1="220" y1="400" x2="314" y2="400" stroke="rgba(0,229,255,0.15)" stroke-width="1.2" stroke-dasharray="6 28" style="animation:fd-flow 3.5s linear infinite;"/>
  <line x1="364" y1="400" x2="502" y2="400" stroke="rgba(0,229,255,0.13)" stroke-width="1.2" stroke-dasharray="6 28" style="animation:fd-flow 3.5s linear infinite 0.4s;"/>
  <path d="M 526,388 Q 600,290 716,290" stroke="rgba(0,229,255,0.10)" stroke-width="1.2" fill="none" stroke-dasharray="6 28" style="animation:fd-flow 4s linear infinite 0.8s;"/>
  <line x1="526" y1="400" x2="716" y2="400" stroke="rgba(0,229,255,0.11)" stroke-width="1.2" stroke-dasharray="6 28" style="animation:fd-flow 3.5s linear infinite 0.6s;"/>
  <path d="M 526,412 Q 600,510 716,510" stroke="rgba(0,229,255,0.08)" stroke-width="1.2" fill="none" stroke-dasharray="6 28" style="animation:fd-flow 4s linear infinite 1.0s;"/>
  <path d="M 740,290 Q 840,290 888,374" stroke="rgba(0,229,255,0.08)" stroke-width="1.2" fill="none" stroke-dasharray="6 28" style="animation:fd-flow 4.5s linear infinite 1.4s;"/>
  <line x1="740" y1="400" x2="888" y2="400" stroke="rgba(0,229,255,0.11)" stroke-width="1.2" stroke-dasharray="6 28" style="animation:fd-flow 3.5s linear infinite 1.0s;"/>
  <path d="M 740,510 Q 840,510 888,426" stroke="rgba(0,229,255,0.07)" stroke-width="1.2" fill="none" stroke-dasharray="6 28" style="animation:fd-flow 4.5s linear infinite 1.8s;"/>
  <!-- Complaint rect -->
  <rect x="140" y="374" width="80" height="52" rx="5" fill="rgba(0,229,255,0.03)" stroke="rgba(0,229,255,0.1)" stroke-width="1.2"/>
  <line x1="154" y1="388" x2="206" y2="388" stroke="rgba(0,229,255,0.07)" stroke-width="1"/>
  <line x1="154" y1="397" x2="202" y2="397" stroke="rgba(0,229,255,0.05)" stroke-width="1"/>
  <line x1="154" y1="406" x2="196" y2="406" stroke="rgba(0,229,255,0.04)" stroke-width="1"/>
  <line x1="154" y1="415" x2="188" y2="415" stroke="rgba(0,229,255,0.03)" stroke-width="1"/>
  <!-- Classify circle -->
  <circle cx="338" cy="400" r="26" fill="rgba(0,229,255,0.03)" stroke="rgba(0,229,255,0.1)" stroke-width="1.2"/>
  <!-- Route diamond -->
  <polygon points="526,376 550,400 526,424 502,400" fill="rgba(0,229,255,0.03)" stroke="rgba(0,229,255,0.1)" stroke-width="1.2"/>
  <!-- Agent circles -->
  <circle cx="728" cy="290" r="20" fill="rgba(0,229,255,0.03)" stroke="rgba(0,229,255,0.09)" stroke-width="1.2"/>
  <circle cx="728" cy="400" r="20" fill="rgba(0,229,255,0.03)" stroke="rgba(0,229,255,0.09)" stroke-width="1.2"/>
  <circle cx="728" cy="510" r="20" fill="rgba(0,229,255,0.03)" stroke="rgba(0,229,255,0.09)" stroke-width="1.2"/>
  <!-- Resolved circle + check -->
  <circle cx="916" cy="400" r="28" fill="rgba(76,217,123,0.04)" stroke="rgba(76,217,123,0.13)" stroke-width="1.2"/>
  <path d="M 906,400 L 912,408 L 926,392" stroke="rgba(76,217,123,0.2)" stroke-width="1.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
</div>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "landing"
if "user_name" not in st.session_state:
    st.session_state.user_name = ""

# ── Navbar ────────────────────────────────────────────────────────────────
back_label = "← Back" if st.session_state.page != "landing" else ""
nav_col1, nav_col2 = st.columns([8, 1])
with nav_col1:
    st.markdown("""
    <div class="fd-navbar">
      <div class="fd-brand">
        <svg class="fd-brand-icon" width="64" height="44" viewBox="0 0 64 44" fill="none" xmlns="http://www.w3.org/2000/svg">
          <!-- Complaint ticket -->
          <rect x="1" y="4" width="20" height="28" rx="4" fill="rgba(0,229,255,0.06)" stroke="#00E5FF" stroke-width="1.4"/>
          <rect x="5" y="9"  width="3" height="3" rx="1" fill="#00E5FF" opacity="0.7"/>
          <line x1="11" y1="10.5" x2="18" y2="10.5" stroke="#00E5FF" stroke-width="1.2" stroke-linecap="round" opacity="0.5"/>
          <rect x="5" y="15" width="3" height="3" rx="1" fill="#00E5FF" opacity="0.7"/>
          <line x1="11" y1="16.5" x2="18" y2="16.5" stroke="#00E5FF" stroke-width="1.2" stroke-linecap="round" opacity="0.5"/>
          <rect x="5" y="21" width="3" height="3" rx="1" fill="#00E5FF" opacity="0.4"/>
          <line x1="11" y1="22.5" x2="15" y2="22.5" stroke="#00E5FF" stroke-width="1.2" stroke-linecap="round" opacity="0.3"/>
          <!-- Arrow -->
          <path d="M25 22 L38 22" stroke="rgba(0,229,255,0.4)" stroke-width="1.4" stroke-linecap="round"/>
          <path d="M35 18.5 L39 22 L35 25.5" stroke="rgba(0,229,255,0.4)" stroke-width="1.4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
          <!-- Resolved badge -->
          <circle cx="51" cy="22" r="11" fill="rgba(76,217,123,0.08)" stroke="#4CD97B" stroke-width="1.4"/>
          <path d="M45.5 22 L49.5 26 L56.5 17" stroke="#4CD97B" stroke-width="1.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <div>
          <div class="fd-logo">FlowDesk</div>
          <div class="fd-tagline">Autonomous Campus Issue Resolution</div>
        </div>
      </div>
      <div class="fd-status">
        <div class="fd-dot"></div>
        All systems online
      </div>
    </div>
    """, unsafe_allow_html=True)
with nav_col2:
    if st.session_state.page != "landing":
        st.markdown("<div style='padding-top:1.2rem'>", unsafe_allow_html=True)
        if st.button("← Home", use_container_width=True):
            st.session_state.page = "landing"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


# ── Page routing ──────────────────────────────────────────────────────────
from pages import admin_dashboard, student_portal  # noqa: E402

page = st.session_state.page

# ── Landing page ──────────────────────────────────────────────────────────
if page == "landing":
    st.markdown("""
    <div class="fd-hero">
        <div class="fd-hero-title">FlowDesk</div>
        <div class="fd-headline">
            From <span class="fd-strike">&ldquo;we&rsquo;ll look into it&rdquo;<svg class="fd-strike-svg" viewBox="0 0 100 100" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg"><path d="M -2,82 Q 48,52 102,18" stroke="rgba(224,230,244,0.30)" stroke-width="3.5" fill="none" stroke-linecap="round"/></svg></span> to <span style="color:#00E5FF;font-weight:700;">done</span>
        </div>
        <div class="fd-hero-sub">Autonomous · Multi-Agent · Real-Time</div>
        <div class="fd-hero-divider"></div>
    </div>
    """, unsafe_allow_html=True)

    _, c1, c2, _ = st.columns([1, 2, 2, 1])

    with c1:
        st.markdown("""
        <div class="role-card role-card-student">
            <div class="role-icon"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#00E5FF" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg></div>
            <div class="role-title role-title-student">Student Portal</div>
            <div class="role-desc">Submit complaints, track your tickets, and get real-time updates on resolution status.</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='margin-top:1rem'/>", unsafe_allow_html=True)
        if st.button("Enter as Student →", key="btn_student", use_container_width=True, type="primary"):
            st.session_state.page = "login_student"
            st.rerun()

    with c2:
        st.markdown("""
        <div class="role-card role-card-admin">
            <div class="role-icon"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#FFA500" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><line x1="21" y1="4" x2="14" y2="4"/><line x1="10" y1="4" x2="3" y2="4"/><line x1="21" y1="12" x2="12" y2="12"/><line x1="8" y1="12" x2="3" y2="12"/><line x1="21" y1="20" x2="16" y2="20"/><line x1="12" y1="20" x2="3" y2="20"/><line x1="14" y1="2" x2="14" y2="6"/><line x1="8" y1="10" x2="8" y2="14"/><line x1="16" y1="18" x2="16" y2="22"/></svg></div>
            <div class="role-title role-title-admin">Admin Dashboard</div>
            <div class="role-desc">Full system oversight — metrics, SLA enforcement, escalations, and analytics.</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='margin-top:1rem'/>", unsafe_allow_html=True)
        if st.button("Enter as Admin →", key="btn_admin", use_container_width=True, type="primary"):
            st.session_state.page = "login_admin"
            st.rerun()

# ── Login: Student ─────────────────────────────────────────────────────────
elif page == "login_student":
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown("""
        <div class="login-header">
            <div class="login-title" style="color:#00E5FF"><svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#00E5FF" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg> Student Login</div>
            <div class="login-back">Enter your Telegram ID to access your tickets</div>
        </div>
        """, unsafe_allow_html=True)
        telegram_id = st.text_input("Telegram ID", placeholder="e.g. @yourusername")
        name = st.text_input("Your Name", placeholder="e.g. Rahul Sharma")
        st.markdown("<div style='margin-top:1rem'/>", unsafe_allow_html=True)
        if st.button("Access Student Portal →", use_container_width=True, type="primary"):
            if telegram_id.strip():
                st.session_state.user_name = name or telegram_id
                st.session_state.student_telegram_id = telegram_id.strip()
                st.session_state.page = "portal_student"
                st.rerun()
            else:
                st.error("Please enter your Telegram ID.")


# ── Login: Admin ───────────────────────────────────────────────────────────
elif page == "login_admin":
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown("""
        <div class="login-header">
            <div class="login-title" style="color:#FFA500"><svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#FFA500" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><line x1="21" y1="4" x2="14" y2="4"/><line x1="10" y1="4" x2="3" y2="4"/><line x1="21" y1="12" x2="12" y2="12"/><line x1="8" y1="12" x2="3" y2="12"/><line x1="21" y1="20" x2="16" y2="20"/><line x1="12" y1="20" x2="3" y2="20"/><line x1="14" y1="2" x2="14" y2="6"/><line x1="8" y1="10" x2="8" y2="14"/><line x1="16" y1="18" x2="16" y2="22"/></svg> Admin Login</div>
            <div class="login-back">Enter the admin key to access full system controls</div>
        </div>
        """, unsafe_allow_html=True)
        admin_key = st.text_input("Admin Key", type="password", placeholder="Enter admin key")
        st.markdown("<div style='margin-top:1rem'/>", unsafe_allow_html=True)
        if st.button("Access Admin Dashboard →", use_container_width=True, type="primary"):
            if admin_key.strip():
                st.session_state.page = "portal_admin"
                st.rerun()
            else:
                st.error("Please enter the admin key.")

# ── Portals ────────────────────────────────────────────────────────────────
elif page == "portal_student":
    student_portal.render()


elif page == "portal_admin":
    admin_dashboard.render()
