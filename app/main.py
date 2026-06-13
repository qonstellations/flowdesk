import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from dotenv import load_dotenv

import backend.db as db

load_dotenv()

st.set_page_config(
    page_title="FlowDesk",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Loader — injected before CSS block, navbar, and all page content.
# session_state gate ensures it only plays once per session, not on every Streamlit rerender.
if not st.session_state.get("_loader_shown"):
    st.session_state["_loader_shown"] = True
    st.html("""
<style>
@keyframes _fd_bar{0%{width:0}40%{width:60%}75%{width:87%}92%{width:97%}100%{width:100%}}
@keyframes _fd_out{0%{opacity:1}100%{opacity:0;visibility:hidden}}
</style>
<div style="position:fixed;inset:0;background:#050C1A;z-index:99999;
            display:flex;flex-direction:column;align-items:center;justify-content:center;
            pointer-events:none;animation:_fd_out .45s ease-out 3.2s forwards;">
  <div style="font-size:2.6rem;font-weight:900;letter-spacing:-.04em;color:#00E5FF;
              text-shadow:0 0 32px rgba(0,229,255,.35);margin-bottom:1.8rem;">FlowDesk</div>
  <div style="width:360px;height:5px;background:rgba(255,255,255,.07);border-radius:3px;overflow:hidden;">
    <div style="height:100%;width:0%;border-radius:3px;
                background:linear-gradient(90deg,#00E5FF,#7C4DFF);
                box-shadow:0 0 14px rgba(0,229,255,.5);
                animation:_fd_bar 3.2s cubic-bezier(.4,0,.2,1) forwards;"></div>
  </div>
  <div style="margin-top:1.1rem;font-size:.68rem;letter-spacing:.2em;
              color:#3A4468;text-transform:uppercase;">Autonomous Campus Issue Resolution</div>
</div>
""")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700;800;900&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Space Grotesk', sans-serif !important;
}
.stApp {
    background-color: #050C1A;
    background-image:
        radial-gradient(ellipse 60% 40% at 15% 60%, rgba(0,229,255,0.055) 0%, transparent 70%),
        radial-gradient(ellipse 50% 50% at 85% 15%, rgba(124,77,255,0.07) 0%, transparent 70%),
        linear-gradient(160deg, #050C1A 0%, #062233 50%, #073D50 100%);
    color: #E0E6F4;
}

/* ── Hide sidebar entirely ─────────────────────────── */
section[data-testid="stSidebar"]          { display: none !important; }
button[data-testid="collapsedControl"]    { display: none !important; }
[data-testid="stDecoration"]              { display: none !important; }

/* ── Remove Streamlit default top padding ──────────── */
.block-container { padding-top: 0 !important; }
[data-testid="stMain"] > div:first-child { padding-top: 0 !important; }

/* ── Flush navbar column to left edge ──────────────── */
.block-container > div:first-child div[data-testid="stHorizontalBlock"] > div:first-child {
    padding-left: 0 !important;
}

/* ── Top navbar ────────────────────────────────────── */
.fd-navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 16px 10px 0;
    background: transparent;
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
    position: relative;
    overflow: hidden;
}
.fd-hero-title {
    font-size: clamp(5rem, 14vw, 11rem);
    font-weight: 900;
    letter-spacing: -0.06em;
    line-height: 0.95;
    color: #E0E6F4;
    margin-bottom: 1.5rem;
    position: relative;
    z-index: 2;
}
.fd-hero-sub {
    font-size: 1rem;
    color: rgba(224,230,244,0.62);
    letter-spacing: 0.04em;
    font-weight: 400;
    margin-bottom: 0.5rem;
    position: relative;
    z-index: 2;
}
.fd-hero-divider {
    width: 60px;
    height: 2px;
    background: #00E5FF;
    margin: 1.2rem auto 3rem;
    border-radius: 2px;
    position: relative;
    z-index: 2;
}

/* ── Drifting background words ─────────────────────── */
@keyframes fd-drift {
    0%   { opacity: 0; transform: translateY(0px); }
    12%  { opacity: 1; }
    88%  { opacity: 1; }
    100% { opacity: 0; transform: translateY(-32px); }
}
.fd-drift-word {
    position: absolute;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    color: rgba(0,229,255,0.5);
    pointer-events: none;
    white-space: nowrap;
    animation: fd-drift 11s ease-in-out infinite;
    opacity: 0;
    z-index: 0;
    user-select: none;
    text-transform: uppercase;
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
    color: #9AAAC8;
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
    font-size: clamp(1.25rem, 3vw, 2rem);
    font-weight: 400;
    color: rgba(224,230,244,0.78);
    letter-spacing: -0.01em;
    line-height: 1.5;
    margin-bottom: 2rem;
    position: relative;
    z-index: 2;
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

/* ── Portal entrance animation ─────────────────────── */
@keyframes fd-page-in {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ── Zoom-through transition ───────────────────────── */
@keyframes fd-zoom-through {
    0%   { opacity: 1; transform: scale(1); }
    100% { opacity: 0; transform: scale(5); }
}

/* ── Landing section bands ─────────────────────────── */
.fd-section-band {
    max-width: 880px;
    margin: 0 auto;
    padding: 3.5rem 2rem;
    border-top: 1px solid rgba(0,229,255,0.06);
    text-align: center;
}
.fd-band-label {
    font-size: 1rem;
    letter-spacing: 0.24em;
    text-transform: uppercase;
    color: #00E5FF;
    font-weight: 600;
    margin-bottom: 0.5rem;
    opacity: 0.6;
}
.fd-band-title {
    font-size: clamp(2.4rem, 5vw, 3.5rem);
    font-weight: 800;
    letter-spacing: -0.03em;
    color: #C8D0E8;
    margin-bottom: 1.5rem;
    line-height: 1.2;
}

/* ── Content panel ─────────────────────────────────── */
.fd-panel {
    background: linear-gradient(155deg, rgba(14,22,48,0.96) 0%, rgba(10,16,34,0.99) 100%);
    border: 1px solid rgba(0,229,255,0.1);
    border-radius: 20px;
    padding: 2rem 2.4rem;
    box-shadow: 0 4px 30px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.03);
    position: relative;
    overflow: hidden;
}
.fd-panel::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(0,229,255,0.22), transparent);
}
.fd-problem-text {
    font-size: 1.35rem;
    color: rgba(224,230,244,0.68);
    line-height: 1.85;
    margin: 0;
    text-align: center;
}

/* ── How It Works ──────────────────────────────────── */
.fd-steps {
    display: flex;
    align-items: flex-start;
    width: 100%;
}
.fd-step {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 1.4rem 0.6rem;
}
.fd-step-icon {
    width: 50px; height: 50px;
    border-radius: 14px;
    border: 1px solid rgba(0,229,255,0.2);
    background: rgba(0,229,255,0.05);
    display: flex; align-items: center; justify-content: center;
    margin-bottom: 0.85rem;
    flex-shrink: 0;
}
.fd-step-num {
    font-size: 0.85rem;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: rgba(0,229,255,0.45);
    font-weight: 600;
    margin-bottom: 0.3rem;
}
.fd-step-label {
    font-size: 1.15rem;
    font-weight: 700;
    color: #C8D0E8;
    margin-bottom: 0.3rem;
    letter-spacing: -0.01em;
}
.fd-step-desc {
    font-size: 1.05rem;
    color: rgba(224,230,244,0.4);
    line-height: 1.55;
}
.fd-step-connector {
    flex-shrink: 0;
    display: flex;
    align-items: center;
    padding-top: 25px;
}

/* ── Feature cards ─────────────────────────────────── */
.fd-features-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
}
.fd-feature-card {
    background: linear-gradient(155deg, rgba(18,26,50,0.95) 0%, rgba(12,18,36,0.98) 100%);
    border: 1px solid rgba(0,229,255,0.12);
    border-radius: 18px;
    padding: 1.5rem 1.6rem;
    position: relative;
    overflow: hidden;
    transition: all 0.25s ease;
    box-shadow: 0 2px 20px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.03);
    text-align: center;
}
.fd-feature-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(0,229,255,0.28), transparent);
}
.fd-feature-card:hover {
    transform: translateY(-4px);
    border-color: rgba(0,229,255,0.24);
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}
.fd-feature-label {
    font-size: 1.25rem;
    font-weight: 700;
    color: #C8D0E8;
    margin-bottom: 0.35rem;
    letter-spacing: -0.01em;
}
.fd-feature-desc {
    font-size: 1.05rem;
    color: rgba(224,230,244,0.42);
    line-height: 1.55;
    margin: 0;
}

/* ── Mockup frames ─────────────────────────────────── */
.fd-mockup-wrap {
    display: flex;
    gap: 1.5rem;
    justify-content: center;
    flex-wrap: wrap;
}
.fd-mockup-frame {
    flex: 1;
    min-width: 220px;
    max-width: 390px;
    border: 1px solid rgba(0,229,255,0.14);
    border-radius: 18px;
    overflow: hidden;
    background: rgba(10,16,34,0.98);
    box-shadow: 0 8px 40px rgba(0,0,0,0.5);
}
.fd-mockup-bar {
    background: rgba(14,22,48,0.98);
    border-bottom: 1px solid rgba(0,229,255,0.07);
    padding: 10px 16px;
    display: flex;
    align-items: center;
    gap: 5px;
}
.fd-mockup-dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: rgba(255,255,255,0.07);
}
.fd-mockup-title {
    font-size: 0.67rem;
    color: rgba(224,230,244,0.28);
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-left: 7px;
}
.fd-mockup-body {
    height: 188px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: rgba(224,230,244,0.13);
    font-size: 0.68rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    border: 1px dashed rgba(0,229,255,0.07);
    margin: 1rem;
    border-radius: 10px;
}

/* ── CTA line ──────────────────────────────────────── */
.fd-cta-line {
    text-align: center;
    font-size: 1.2rem;
    color: rgba(224,230,244,0.55);
    margin-bottom: 2rem;
    font-weight: 400;
    letter-spacing: -0.01em;
}

/* ── Responsive ────────────────────────────────────── */
@media (max-width: 640px) {
    .fd-steps { flex-direction: column; align-items: center; }
    .fd-step-connector { display: none; }
    .fd-features-grid { grid-template-columns: 1fr; }
    .fd-mockup-wrap { flex-direction: column; align-items: center; }
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

user = getattr(st, "user", None)
is_google_student_logged_in = bool(user and getattr(user, "is_logged_in", False))
if is_google_student_logged_in and st.session_state.page in ("landing", "login_student") and not st.session_state.pop("_nav_override", False):
    st.session_state.page = "portal_student"

# ── Navbar ────────────────────────────────────────────────────────────────
_back_dest = {
    "login_student": "landing",
    "login_admin":   "landing",
    "portal_student": "landing",
    "portal_admin":   "login_admin",
}.get(st.session_state.page, "landing")

nav_col1, nav_col2 = st.columns([5, 4])
with nav_col1:
    st.markdown("""
    <div class="fd-navbar">
      <div class="fd-brand">
        <svg class="fd-brand-icon" width="64" height="44" viewBox="0 0 64 44" fill="none" xmlns="http://www.w3.org/2000/svg">
          <!-- Phone body -->
          <rect x="0" y="2" width="22" height="40" rx="4" fill="rgba(0,229,255,0.06)" stroke="#00E5FF" stroke-width="1.4"/>
          <!-- Camera dot -->
          <circle cx="11" cy="5" r="1" fill="#00E5FF" opacity="0.4"/>
          <!-- Screen -->
          <rect x="2.5" y="8" width="17" height="22" rx="2" fill="rgba(0,229,255,0.04)" stroke="rgba(0,229,255,0.2)" stroke-width="0.8"/>
          <!-- Telegram paper plane inside screen -->
          <path d="M5,23 L19,11 L15,27 Z" fill="rgba(0,229,255,0.3)" stroke="#00E5FF" stroke-width="1" stroke-linejoin="round"/>
          <line x1="5" y1="23" x2="11" y2="19" stroke="#00E5FF" stroke-width="0.8" stroke-linecap="round" opacity="0.55"/>
          <line x1="11" y1="19" x2="15" y2="27" stroke="#00E5FF" stroke-width="0.8" stroke-linecap="round" opacity="0.55"/>
          <!-- Home button -->
          <circle cx="11" cy="38" r="2" fill="none" stroke="#00E5FF" stroke-width="1" opacity="0.4"/>
          <!-- Arrow -->
          <path d="M26 22 L36 22" stroke="rgba(0,229,255,0.4)" stroke-width="1.4" stroke-linecap="round"/>
          <path d="M33 18.5 L37 22 L33 25.5" stroke="rgba(0,229,255,0.4)" stroke-width="1.4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
          <!-- Resolved badge -->
          <circle cx="52" cy="22" r="11" fill="rgba(76,217,123,0.08)" stroke="#4CD97B" stroke-width="1.4"/>
          <path d="M46.5 22 L50.5 26 L57.5 17" stroke="#4CD97B" stroke-width="1.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
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
        nb1, nb2 = st.columns(2)
        with nb1:
            if st.button("⌂ Home", use_container_width=True, key="nav_home"):
                st.session_state["_nav_override"] = True
                st.session_state.page = "landing"
                st.rerun()
        with nb2:
            if st.button("← Back", use_container_width=True, key="nav_back"):
                st.session_state["_nav_override"] = True
                st.session_state.page = _back_dest
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


# ── Page routing ──────────────────────────────────────────────────────────
from pages import admin_dashboard, student_portal  # noqa: E402

page = st.session_state.page
prev_page = st.session_state.get("_prev_page", "")
st.session_state["_prev_page"] = page

# ── Landing page ──────────────────────────────────────────────────────────
if page == "landing":

    # === HERO ===
    st.markdown("""
    <div class="fd-hero">
        <div class="fd-drift-word" style="top:18%;left:22%;animation-delay:0s;animation-duration:12s;">❄️ Broken AC</div>
        <div class="fd-drift-word" style="top:55%;left:58%;animation-delay:2.5s;animation-duration:14s;">📶 No WiFi</div>
        <div class="fd-drift-word" style="top:30%;left:62%;animation-delay:5.0s;animation-duration:11s;">🛏️ Hostel mess</div>
        <div class="fd-drift-word" style="top:68%;left:25%;animation-delay:1.6s;animation-duration:13s;">💧 Water leak</div>
        <div class="fd-drift-word" style="top:12%;left:42%;animation-delay:7.2s;animation-duration:15s;">📚 Library hours</div>
        <div class="fd-drift-word" style="top:78%;left:46%;animation-delay:3.8s;animation-duration:12s;">🍽️ Mess food</div>
        <div style="position:relative;z-index:2;">
            <div class="fd-hero-title">FlowDesk</div>
            <div class="fd-headline">
                From <span class="fd-strike">&ldquo;we&rsquo;ll look into it&rdquo;<svg class="fd-strike-svg" viewBox="0 0 100 100" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg"><path d="M -2,82 Q 48,52 102,18" stroke="rgba(224,230,244,0.30)" stroke-width="3.5" fill="none" stroke-linecap="round"/></svg></span> to <span style="color:#00E5FF;font-weight:700;">done</span>
            </div>
            <div class="fd-hero-sub">File a campus complaint by text. Our AI routes it, tracks it, and makes sure it actually gets solved.</div>
            <div class="fd-hero-divider"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # === THE PROBLEM ===
    st.markdown("""
    <div class="fd-section-band">
        <div class="fd-band-label">The Problem</div>
        <div class="fd-band-title">Why complaints go nowhere</div>
        <div class="fd-panel">
            <p class="fd-problem-text">You report a broken fan, someone says they'll handle it, and three weeks later you're still sweating. Campus complaints get lost in inboxes, passed around, and forgotten. FlowDesk makes sure they don't.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # === HOW IT WORKS ===
    st.markdown("""
    <div class="fd-section-band">
        <div class="fd-band-label">How It Works</div>
        <div class="fd-band-title">Four steps, zero follow-up emails</div>
        <div class="fd-steps">
            <div class="fd-step">
                <div class="fd-step-icon">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#00E5FF" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                    </svg>
                </div>
                <div class="fd-step-num">Step 01</div>
                <div class="fd-step-label">Text the bot</div>
                <div class="fd-step-desc">File a complaint on Telegram. No app, no forms.</div>
            </div>
            <div class="fd-step-connector">
                <svg width="28" height="16" viewBox="0 0 28 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <line x1="0" y1="8" x2="20" y2="8" stroke="rgba(0,229,255,0.28)" stroke-width="1.2"/>
                    <polyline points="16,4 22,8 16,12" stroke="rgba(0,229,255,0.28)" stroke-width="1.2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <div class="fd-step">
                <div class="fd-step-icon">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#00E5FF" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="2" y="2" width="20" height="20" rx="2"/><line x1="8" y1="2" x2="8" y2="22"/><line x1="16" y1="2" x2="16" y2="22"/><line x1="2" y1="8" x2="22" y2="8"/><line x1="2" y1="16" x2="22" y2="16"/>
                    </svg>
                </div>
                <div class="fd-step-num">Step 02</div>
                <div class="fd-step-label">AI sorts it out</div>
                <div class="fd-step-desc">Agents classify your issue and route it to the right department.</div>
            </div>
            <div class="fd-step-connector">
                <svg width="28" height="16" viewBox="0 0 28 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <line x1="0" y1="8" x2="20" y2="8" stroke="rgba(0,229,255,0.28)" stroke-width="1.2"/>
                    <polyline points="16,4 22,8 16,12" stroke="rgba(0,229,255,0.28)" stroke-width="1.2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <div class="fd-step">
                <div class="fd-step-icon">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#00E5FF" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
                        <polyline points="15,15 16,16.5 18,14"/>
                    </svg>
                </div>
                <div class="fd-step-num">Step 03</div>
                <div class="fd-step-label">Assigned with a deadline</div>
                <div class="fd-step-desc">Every complaint gets an owner and a time to resolve.</div>
            </div>
            <div class="fd-step-connector">
                <svg width="28" height="16" viewBox="0 0 28 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <line x1="0" y1="8" x2="20" y2="8" stroke="rgba(0,229,255,0.28)" stroke-width="1.2"/>
                    <polyline points="16,4 22,8 16,12" stroke="rgba(0,229,255,0.28)" stroke-width="1.2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <div class="fd-step">
                <div class="fd-step-icon">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#4CD97B" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                    </svg>
                </div>
                <div class="fd-step-num">Step 04</div>
                <div class="fd-step-label">Tracked till it's done</div>
                <div class="fd-step-desc">Watch it move, and it escalates if it goes overdue.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # === KEY FEATURES ===
    st.markdown("""
    <div class="fd-section-band">
        <div class="fd-band-label">Key Features</div>
        <div class="fd-band-title">Built to stop things slipping</div>
        <div class="fd-features-grid">
            <div class="fd-feature-card">
                <div class="fd-feature-label">Telegram intake</div>
                <p class="fd-feature-desc">Just text. No app to install, no login walls.</p>
            </div>
            <div class="fd-feature-card">
                <div class="fd-feature-label">Autonomous routing</div>
                <p class="fd-feature-desc">AI agents decide where each complaint goes, not a tired admin.</p>
            </div>
            <div class="fd-feature-card">
                <div class="fd-feature-label">Runs anywhere</div>
                <p class="fd-feature-desc">Works on Gemini, OpenAI, or fully offline with a local model.</p>
            </div>
            <div class="fd-feature-card">
                <div class="fd-feature-label">Nothing slips</div>
                <p class="fd-feature-desc">Overdue complaints escalate automatically. No more silence.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # === CALL TO ACTION + PORTAL CARDS ===
    st.markdown("""
    <div class="fd-section-band" style="padding-bottom:0.5rem;">
        <div class="fd-cta-line">Ready to stop chasing complaints? Pick your portal.</div>
    </div>
    """, unsafe_allow_html=True)

    _, c1, c2, _ = st.columns([1, 2, 2, 1], gap="large")

    with c1:
        st.html("""
        <div class="role-card role-card-student">
            <div class="role-icon"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#00E5FF" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg></div>
            <div class="role-title role-title-student">Student Portal</div>
            <div class="role-desc">Submit complaints, track your tickets, and get real-time updates on resolution status.</div>
        </div>
        """)
        st.html("<div style='margin-top:1rem'></div>")
        if st.button("Enter as Student →", key="btn_student", use_container_width=True, type="primary"):
            st.session_state.page = "login_student"
            st.rerun()

    with c2:
        st.html("""
        <div class="role-card role-card-admin">
            <div class="role-icon"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#FFA500" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><line x1="21" y1="4" x2="14" y2="4"/><line x1="10" y1="4" x2="3" y2="4"/><line x1="21" y1="12" x2="12" y2="12"/><line x1="8" y1="12" x2="3" y2="12"/><line x1="21" y1="20" x2="16" y2="20"/><line x1="12" y1="20" x2="3" y2="20"/><line x1="14" y1="2" x2="14" y2="6"/><line x1="8" y1="10" x2="8" y2="14"/><line x1="16" y1="18" x2="16" y2="22"/></svg></div>
            <div class="role-title role-title-admin">Admin Dashboard</div>
            <div class="role-desc">Full system oversight — metrics, target resolution, escalations, and analytics.</div>
        </div>
        """)
        st.html("<div style='margin-top:1rem'></div>")
        if st.button("Enter as Admin →", key="btn_admin", use_container_width=True, type="primary"):
            st.session_state.page = "login_admin"
            st.rerun()

    st.markdown("<div style='height:5rem'/>", unsafe_allow_html=True)

# ── Login: Student ─────────────────────────────────────────────────────────
elif page == "login_student":
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown("""
        <div class="login-header">
            <div class="login-title" style="color:#00E5FF"><svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#00E5FF" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg> Student Login</div>
            <div class="login-back">Sign in with Google to access your tickets</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='margin-top:1rem'/>", unsafe_allow_html=True)
        user = getattr(st, "user", None)
        is_logged_in = bool(user and getattr(user, "is_logged_in", False))
        if is_logged_in:
            st.session_state.page = "portal_student"
            st.rerun()
        else:
            student_portal.render_login_button()


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
            expected_key = os.getenv("ADMIN_KEY", "").strip()
            if not expected_key:
                st.error("ADMIN_KEY is not configured.")
            elif admin_key.strip() == expected_key:
                st.session_state.page = "portal_admin"
                st.rerun()
            else:
                st.error("Invalid admin key.")

# ── Portals ────────────────────────────────────────────────────────────────
elif page == "portal_student":
    st.markdown("""<style>[data-testid="stMainBlockContainer"]{animation:fd-page-in 0.45s ease-out both;}</style>""", unsafe_allow_html=True)
    if prev_page != "portal_student":
        st.markdown('<div style="position:fixed;top:0;left:0;width:100vw;height:100vh;background:radial-gradient(ellipse at center,rgba(0,229,255,0.9) 0%,rgba(0,229,255,0.4) 20%,rgba(0,229,255,0.08) 45%,#070C18 68%);z-index:9999;pointer-events:none;transform-origin:center center;animation:fd-zoom-through 0.55s cubic-bezier(0.25,0,0.5,1) forwards;"></div>', unsafe_allow_html=True)
    student_portal.render()


elif page == "portal_admin":
    st.markdown("""<style>[data-testid="stMainBlockContainer"]{animation:fd-page-in 0.45s ease-out both;}</style>""", unsafe_allow_html=True)
    if prev_page != "portal_admin":
        st.markdown('<div style="position:fixed;top:0;left:0;width:100vw;height:100vh;background:radial-gradient(ellipse at center,rgba(255,165,0,0.9) 0%,rgba(255,165,0,0.4) 20%,rgba(255,165,0,0.08) 45%,#070C18 68%);z-index:9999;pointer-events:none;transform-origin:center center;animation:fd-zoom-through 0.55s cubic-bezier(0.25,0,0.5,1) forwards;"></div>', unsafe_allow_html=True)
    admin_dashboard.render()
