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
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

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
    padding: 14px 28px;
    background: rgba(12, 18, 34, 0.88);
    border-bottom: 1px solid rgba(0,229,255,0.1);
    backdrop-filter: blur(16px);
    border-radius: 0 0 18px 18px;
    margin-bottom: 28px;
}
.fd-logo {
    font-size: 1.7rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    background: linear-gradient(100deg, #00E5FF 0%, #7C4DFF 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
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

/* ── Flow pipeline ─────────────────────────────────── */
.fd-pipeline {
    display: flex;
    justify-content: center;
    align-items: center;
    flex-wrap: wrap;
    gap: 6px;
    margin: 0 0 24px;
}
.fd-step {
    background: rgba(16,24,46,0.8);
    border: 1px solid rgba(0,229,255,0.18);
    border-radius: 9px;
    padding: 7px 15px;
    font-size: 0.82rem;
    color: #9AAAC8;
    white-space: nowrap;
}
.fd-arrow { color: #00E5FF80; font-size: 1rem; }

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
    box-shadow: 0 8px 32px rgba(0,229,255,0.12), inset 0 1px 0 rgba(255,255,255,0.06);
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
/* Inactive pills */
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
    box-shadow: 0 6px 24px rgba(0,229,255,0.18) !important;
}
/* Active / selected pill */
[data-testid="stBaseButton-pillsActive"] {
    background: linear-gradient(135deg, rgba(0,229,255,0.22), rgba(124,77,255,0.22)) !important;
    border: 1.5px solid #00E5FF !important;
    border-radius: 14px !important;
    color: #00E5FF !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
    padding: 14px 40px !important;
    letter-spacing: 0.03em !important;
    min-width: 200px !important;
    box-shadow: 0 0 28px rgba(0,229,255,0.28), inset 0 1px 0 rgba(255,255,255,0.1) !important;
    text-shadow: 0 0 14px rgba(0,229,255,0.55) !important;
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
    box-shadow: 0 6px 24px rgba(0,229,255,0.18) !important;
}
div[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #00C4E0, #6B35D9) !important;
    border: none !important;
    color: white !important;
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
</style>
""", unsafe_allow_html=True)

db.init_db()

# ── Navbar ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="fd-navbar">
  <div>
    <div class="fd-logo">⚡ FlowDesk</div>
    <div class="fd-tagline">Autonomous Campus Issue Resolution</div>
  </div>
  <div class="fd-status">
    <div class="fd-dot"></div>
    All systems online
  </div>
</div>
""", unsafe_allow_html=True)

# ── Pipeline diagram ──────────────────────────────────────────────────────
steps = ["📥 Intake", "🤖 AI Classify", "📍 Route", "⏰ SLA Set", "🔔 Notify", "✅ Resolve"]
pipeline_html = '<div class="fd-pipeline">'
for i, s in enumerate(steps):
    pipeline_html += f'<div class="fd-step">{s}</div>'
    if i < len(steps) - 1:
        pipeline_html += '<span class="fd-arrow">→</span>'
pipeline_html += "</div>"
st.markdown(pipeline_html, unsafe_allow_html=True)

# ── Navigation ────────────────────────────────────────────────────────────
_, nav_col, _ = st.columns([0.5, 4, 0.5])
with nav_col:
    page = st.pills(
        "Navigation",
        options=["🎓  Student Portal", "👷  Staff Dashboard", "⚙️  Admin Dashboard"],
        default="⚙️  Admin Dashboard",
        label_visibility="collapsed",
    )

st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
st.markdown("---")

# ── Page routing ──────────────────────────────────────────────────────────
from pages import admin_dashboard, staff_dashboard, student_portal  # noqa: E402

if page == "🎓  Student Portal":
    student_portal.render()
elif page == "👷  Staff Dashboard":
    staff_dashboard.render()
else:
    admin_dashboard.render()
