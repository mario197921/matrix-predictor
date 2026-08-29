import streamlit as st
import requests
import math
import pandas as pd
from datetime import datetime, timezone
import pytz
from dotenv import load_dotenv

# Carica .env in locale (ignorato in produzione su Streamlit Cloud)
load_dotenv()

# ==========================================
# 🎨 UI: MATRIX DESIGN V90 FIXED
# ==========================================
st.set_page_config(page_title="Matrix Bet V90", page_icon="🎯", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

/* ── VARIABILI ─────────────────────────────────────────────── */
:root {
  --bg:          #0f1117;
  --bg2:         #161b27;
  --bg3:         #1e2535;
  --border:      #2a3248;
  --border2:     #3a4560;
  --accent:      #4f8ef7;
  --accent2:     #7c5cfc;
  --green:       #22c55e;
  --green-dim:   #16a34a;
  --orange:      #f59e0b;
  --red:         #ef4444;
  --red-dim:     #dc2626;
  --gold:        #fbbf24;
  --text:        #e8ecf4;
  --text2:       #8b95b0;
  --text3:       #4a5568;
  --radius:      12px;
  --radius-sm:   8px;
  --shadow:      0 4px 24px rgba(0,0,0,0.4);
  --glow-blue:   0 0 20px rgba(79,142,247,0.15);
  --glow-green:  0 0 20px rgba(34,197,94,0.15);
}

/* ── BASE ─────────────────────────────────────────────────── */
.stApp, body, [data-testid="stAppViewContainer"] {
  background-color: var(--bg) !important;
  color: var(--text) !important;
  font-family: 'DM Sans', sans-serif !important;
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] {
  background: var(--bg2) !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }

/* ── TYPOGRAPHY ───────────────────────────────────────────── */
h1, h2, h3 {
  font-family: 'Syne', sans-serif !important;
  color: var(--text) !important;
  letter-spacing: -0.02em;
}
h1 { font-size: 2rem !important; font-weight: 800 !important; }
h2 { font-size: 1.4rem !important; font-weight: 700 !important; }
h3 { font-size: 1.1rem !important; font-weight: 600 !important; }
p, span, label, div { color: var(--text) !important; }

/* ── TABS ─────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
  background: var(--bg2) !important;
  border-radius: var(--radius) !important;
  padding: 4px !important;
  gap: 4px !important;
  border: 1px solid var(--border) !important;
}
.stTabs [data-baseweb="tab"] {
  font-family: 'Syne', sans-serif !important;
  font-weight: 600 !important;
  font-size: 0.85rem !important;
  color: var(--text2) !important;
  background: transparent !important;
  border-radius: var(--radius-sm) !important;
  padding: 8px 16px !important;
  transition: all 0.2s !important;
}
.stTabs [aria-selected="true"] {
  background: var(--accent) !important;
  color: #fff !important;
  box-shadow: var(--glow-blue) !important;
}
.stTabs [data-baseweb="tab-panel"] {
  padding-top: 20px !important;
}

/* ── EXPANDER ─────────────────────────────────────────────── */
.stExpander {
  background: var(--bg2) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  margin-bottom: 8px !important;
  overflow: hidden !important;
  transition: border-color 0.2s, box-shadow 0.2s !important;
}
.stExpander:hover {
  border-color: var(--border2) !important;
  box-shadow: var(--shadow) !important;
}
.stExpander summary {
  font-family: 'DM Sans', sans-serif !important;
  font-weight: 500 !important;
  color: var(--text) !important;
  padding: 14px 18px !important;
}

/* ── METRICS ─────────────────────────────────────────────── */
[data-testid="stMetric"] {
  background: var(--bg3) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  padding: 16px !important;
}
[data-testid="stMetricValue"] {
  font-family: 'Syne', sans-serif !important;
  font-size: 1.6rem !important;
  font-weight: 800 !important;
  color: var(--accent) !important;
}
[data-testid="stMetricLabel"] {
  font-size: 0.75rem !important;
  color: var(--text2) !important;
  text-transform: uppercase !important;
  letter-spacing: 0.08em !important;
}

/* ── BUTTONS ─────────────────────────────────────────────── */
.stButton > button {
  background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
  color: #fff !important;
  border: none !important;
  border-radius: var(--radius-sm) !important;
  font-family: 'Syne', sans-serif !important;
  font-weight: 600 !important;
  font-size: 0.85rem !important;
  padding: 10px 20px !important;
  width: 100% !important;
  transition: opacity 0.2s, transform 0.1s !important;
  box-shadow: 0 2px 12px rgba(79,142,247,0.3) !important;
}
.stButton > button:hover {
  opacity: 0.9 !important;
  transform: translateY(-1px) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* ── INPUTS ─────────────────────────────────────────────── */
.stNumberInput input, .stTextInput input, .stSelectbox select,
[data-testid="stDateInput"] input {
  background: var(--bg3) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
  color: var(--text) !important;
  font-family: 'DM Sans', sans-serif !important;
}
.stMultiSelect [data-baseweb="select"] {
  background: var(--bg3) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
}
/* Pills campionati selezionati — blu invece di rosso/arancione */
.stMultiSelect [data-baseweb="tag"] {
  background-color: rgba(79,142,247,0.20) !important;
  border: 1px solid rgba(79,142,247,0.40) !important;
  border-radius: 999px !important;
}
.stMultiSelect [data-baseweb="tag"] span {
  color: #93c5fd !important;
  font-family: 'DM Sans', sans-serif !important;
  font-size: 0.78rem !important;
}
.stMultiSelect [data-baseweb="tag"] [role="presentation"] {
  color: #93c5fd !important;
}

/* ── DATAFRAME ───────────────────────────────────────────── */
[data-testid="stDataFrame"], .stDataEditor {
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  overflow: hidden !important;
}

/* ── ALERTS ─────────────────────────────────────────────── */
[data-testid="stAlert"] {
  background: var(--bg3) !important;
  border-radius: var(--radius-sm) !important;
  border: 1px solid var(--border) !important;
}

/* ── MATCH CARD ─────────────────────────────────────────── */
.match-card {
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  margin-bottom: 12px;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.match-card:hover {
  border-color: var(--accent);
  box-shadow: var(--glow-blue);
}

/* ── XG BAR ─────────────────────────────────────────────── */
.xg-bar-wrap {
  background: var(--bg3);
  border-radius: 999px;
  height: 6px;
  margin: 6px 0 12px;
  overflow: hidden;
  position: relative;
}
.xg-bar-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.5s ease;
}
.xg-bar-home { background: linear-gradient(90deg, var(--accent), #60a5fa); }
.xg-bar-away { background: linear-gradient(90deg, #f87171, var(--red)); }

/* ── TEAM PANEL ─────────────────────────────────────────── */
.team-panel {
  border-radius: var(--radius);
  padding: 18px;
  position: relative;
  overflow: hidden;
}
.team-panel-home {
  background: linear-gradient(135deg, #0f2040 0%, #1a2e4a 100%);
  border: 1px solid #1e3a5f;
}
.team-panel-away {
  background: linear-gradient(135deg, #200f0f 0%, #2d1515 100%);
  border: 1px solid #3d1515;
}
.team-panel-shine {
  position: absolute; top: 0; right: 0;
  width: 120px; height: 120px;
  border-radius: 50%;
  opacity: 0.06;
  transform: translate(30px, -30px);
}
.team-panel-home .team-panel-shine { background: var(--accent); }
.team-panel-away .team-panel-shine { background: var(--red); }
.team-name {
  font-family: 'Syne', sans-serif;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 4px;
}
.xg-number {
  font-family: 'Syne', sans-serif;
  font-size: 2.2rem;
  font-weight: 800;
  line-height: 1;
  margin: 8px 0;
}
.xg-home { color: var(--accent); }
.xg-away { color: #f87171; }
.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 0;
  border-bottom: 1px solid rgba(255,255,255,0.04);
  font-size: 0.82rem;
}
.stat-label { color: var(--text2); }
.stat-value { color: var(--text); font-weight: 600; font-family: 'DM Mono', monospace; }
.form-char {
  display: inline-block;
  width: 22px; height: 22px;
  border-radius: 4px;
  text-align: center;
  line-height: 22px;
  font-size: 0.7rem;
  font-weight: 700;
  margin-right: 2px;
  font-family: 'DM Mono', monospace;
}
.form-W { background: var(--green); color: #fff; }
.form-D { background: var(--orange); color: #fff; }
.form-L { background: var(--red);   color: #fff; }

/* ── PICK CARD ──────────────────────────────────────────── */
.pick-card {
  background: linear-gradient(135deg, #0d1f3c, #162040);
  border: 1px solid #1e3a6e;
  border-radius: var(--radius);
  padding: 20px;
  text-align: center;
  position: relative;
  overflow: hidden;
}
.pick-card::before {
  content: '';
  position: absolute; top: 0; left: 0; right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--accent), var(--accent2));
}
.pick-sign {
  font-family: 'Syne', sans-serif;
  font-size: 3rem;
  font-weight: 800;
  color: var(--gold);
  line-height: 1;
  margin: 8px 0;
  text-shadow: 0 0 30px rgba(251,191,36,0.3);
}
.pick-prob {
  font-size: 0.85rem;
  color: var(--text2);
  margin-bottom: 8px;
}
.edge-positive {
  display: inline-block;
  background: rgba(34,197,94,0.15);
  border: 1px solid rgba(34,197,94,0.3);
  color: var(--green) !important;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 600;
  font-family: 'DM Mono', monospace;
}
.edge-negative {
  display: inline-block;
  background: rgba(239,68,68,0.15);
  border: 1px solid rgba(239,68,68,0.3);
  color: var(--red) !important;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 600;
  font-family: 'DM Mono', monospace;
}
.kelly-pill {
  display: inline-block;
  background: rgba(124,92,252,0.15);
  border: 1px solid rgba(124,92,252,0.3);
  color: #a78bfa !important;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 600;
  font-family: 'DM Mono', monospace;
  margin-left: 6px;
}
.quota-real {
  display: inline-block;
  background: rgba(34,197,94,0.15);
  border: 1px solid rgba(34,197,94,0.3);
  color: var(--green) !important;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 700;
  font-family: 'DM Mono', monospace;
}
.quota-calc {
  display: inline-block;
  background: rgba(139,149,176,0.15);
  border: 1px solid rgba(139,149,176,0.3);
  color: var(--text2) !important;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 600;
  font-family: 'DM Mono', monospace;
}

/* ── TOP3 CARD ──────────────────────────────────────────── */
.top3-card {
  background: var(--bg3);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
}
.top3-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255,255,255,0.04);
  font-size: 0.85rem;
}
.top3-row:last-child { border-bottom: none; }
.top3-tip { font-weight: 600; color: var(--text); }
.top3-prob { color: var(--text2); font-family: 'DM Mono', monospace; font-size: 0.8rem; }

/* ── STRATEGY BOXES ──────────────────────────────────────── */
.strategy-box {
  border-radius: var(--radius);
  padding: 24px;
  margin-bottom: 16px;
  border: 1px solid var(--border);
}
.safety-bg {
  background: linear-gradient(135deg, #0a1f0f, #0d2415);
  border-color: #1a4a25;
  border-left: 4px solid var(--green);
}
.performance-bg {
  background: linear-gradient(135deg, #1f140a, #241a0d);
  border-color: #4a2e10;
  border-left: 4px solid var(--orange);
}
.risk-bg {
  background: linear-gradient(135deg, #1f0a0a, #240d0d);
  border-color: #4a1010;
  border-left: 4px solid var(--red);
}
.builder-bg {
  background: linear-gradient(135deg, #120d1f, #160f26);
  border-color: #2d1a4a;
  border-left: 4px solid var(--accent2);
}

/* ── SCHEDINA ROW ────────────────────────────────────────── */
.schedina-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: var(--bg3);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  margin-bottom: 6px;
  font-size: 0.85rem;
}
.schedina-match { color: var(--text2); font-size: 0.75rem; margin-top: 2px; }

/* ── BADGE / TAGS ────────────────────────────────────────── */
.tag {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  margin-right: 4px;
  margin-top: 4px;
}
.tag-blu    { background: rgba(79,142,247,0.15); border: 1px solid rgba(79,142,247,0.3); color: #93c5fd !important; }
.tag-giallo { background: rgba(251,191,36,0.12); border: 1px solid rgba(251,191,36,0.3); color: var(--gold) !important; }
.tag-verde  { background: rgba(34,197,94,0.12);  border: 1px solid rgba(34,197,94,0.3);  color: #86efac !important; }
.tag-rosso  { background: rgba(239,68,68,0.12);  border: 1px solid rgba(239,68,68,0.3);  color: #fca5a5 !important; }
.tag-viola  { background: rgba(124,92,252,0.12); border: 1px solid rgba(124,92,252,0.3); color: #c4b5fd !important; }

/* ── SECTION HEADER ──────────────────────────────────────── */
.section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border);
}
.section-icon {
  width: 32px; height: 32px;
  background: linear-gradient(135deg, var(--accent), var(--accent2));
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1rem;
  flex-shrink: 0;
}
.section-title {
  font-family: 'Syne', sans-serif;
  font-size: 1rem;
  font-weight: 700;
  color: var(--text);
}

/* ── STAT PILL ───────────────────────────────────────────── */
.stat-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--bg3);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 4px 12px;
  font-size: 0.8rem;
  margin: 3px;
}
.stat-pill-label { color: var(--text2); }
.stat-pill-value { color: var(--text); font-weight: 600; font-family: 'DM Mono', monospace; }

/* ── DIVIDER ─────────────────────────────────────────────── */
.divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--border), transparent);
  margin: 16px 0;
}

/* ── VS BADGE ────────────────────────────────────────────── */
.vs-badge {
  font-family: 'Syne', sans-serif;
  font-size: 1.4rem;
  font-weight: 800;
  color: var(--border2);
  text-align: center;
  padding-top: 40px;
}

/* ── SIDEBAR HEADER ──────────────────────────────────────── */
.sidebar-logo {
  text-align: center;
  padding: 16px 0 8px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 16px;
}
.sidebar-logo-title {
  font-family: 'Syne', sans-serif;
  font-size: 1.3rem;
  font-weight: 800;
  background: linear-gradient(135deg, var(--accent), var(--accent2));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.sidebar-logo-sub {
  font-size: 0.7rem;
  color: var(--text3) !important;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-top: 2px;
}

/* ── FORM-BOX ────────────────────────────────────────────── */
.form-box { letter-spacing: 2px; font-family: 'DM Mono', monospace; font-weight: bold; }

/* ── MISC LEGACY COMPAT ──────────────────────────────────── */
.ritardo-testo { color: var(--red) !important; font-size: 0.85em; font-weight: bold; }
.dna-testo     { color: #a78bfa !important; font-size: 0.85em; font-weight: bold; }
.orario-match  { color: var(--orange) !important; font-weight: bold; font-family: 'DM Mono', monospace; }
.cs-testo      { color: var(--green) !important; font-weight: bold; }
.fts-testo     { color: var(--red) !important; font-weight: bold; }
.star-testo    { color: var(--red) !important; font-weight: bold; font-size: 0.85em; }
.budget-tag {
  font-size: 1rem; font-weight: 700;
  color: var(--text) !important;
  display: inline-block; padding: 6px 14px;
  background: var(--bg3); border-radius: var(--radius-sm);
  border-left: 3px solid var(--accent);
  margin-bottom: 12px;
}

/* ── FIX CALENDARIO — campo visibile (sidebar) sempre scuro+chiaro ────── */
[data-testid="stDateInput"] > div > div {
  background: var(--bg3) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
}
[data-testid="stDateInput"] input {
  color: var(--text) !important;
  background: var(--bg3) !important;
  caret-color: var(--text) !important;
}
/* Le "pillole" con le date selezionate mostrate nel campo */
[data-testid="stDateInput"] span {
  color: var(--text) !important;
}

/* ── FIX CALENDARIO — popup (sempre chiaro, leggibile ovunque) ────────── */
[data-baseweb="calendar"],
[data-baseweb="datepicker"] {
  background-color: #ffffff !important;
}
[data-baseweb="calendar"] *,
[data-baseweb="datepicker"] * {
  color: #1a1a1a !important;
}
[data-baseweb="calendar"] td,
[data-baseweb="calendar"] th,
[data-baseweb="calendar"] button,
[data-baseweb="calendar"] div {
  background-color: #ffffff !important;
}
[data-baseweb="calendar"] [aria-selected="true"] {
  background-color: var(--accent) !important;
  color: #ffffff !important;
}
[data-baseweb="calendar"] [aria-selected="true"] * {
  color: #ffffff !important;
}
[data-baseweb="calendar"] button:hover {
  background-color: #e8f0fe !important;
}
/* Header mese/anno e frecce navigazione nel popup */
[data-baseweb="calendar"] [role="presentation"] {
  color: #1a1a1a !important;
  background-color: #ffffff !important;
}

/* ── FIX EXPANDER — sempre visibile anche su mobile ──────── */
.stExpander > details > summary {
  background: var(--bg2) !important;
  color: var(--text) !important;
  padding: 14px 18px !important;
  font-weight: 600 !important;
  font-size: 0.92rem !important;
  border-radius: var(--radius) !important;
  display: flex !important;
  align-items: center !important;
  cursor: pointer !important;
  user-select: none !important;
}
.stExpander > details > summary:hover {
  background: var(--bg3) !important;
}
.stExpander > details[open] > summary {
  background: var(--bg3) !important;
  border-bottom: 1px solid var(--border) !important;
  border-radius: var(--radius) var(--radius) 0 0 !important;
}
/* Freccia sempre visibile */
.stExpander > details > summary::marker,
.stExpander > details > summary::-webkit-details-marker {
  color: var(--accent) !important;
}

/* ── FIX H2H POPUP — testo visibile su tema scuro ────────── */
.h2h-box {
  background: var(--bg3) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
  padding: 12px 16px !important;
  font-size: 0.85rem !important;
  color: var(--text) !important;
  line-height: 1.8 !important;
}
.h2h-box b, .h2h-box strong {
  color: var(--accent) !important;
}

/* ── SPINNER / SUCCESS / WARNING ─────────────────────────── */
[data-testid="stAlert"][data-baseweb="notification"] {
  background: var(--bg3) !important;
  border: 1px solid var(--accent) !important;
  color: var(--text) !important;
  border-radius: var(--radius-sm) !important;
}
/* Banner campionati attivi — blu invece di arancione */
[data-testid="stAlert"].stSuccess,
div[data-testid="stAlert"] {
  background: linear-gradient(135deg, #0d1f3c, #162040) !important;
  border: 1px solid var(--accent) !important;
  color: var(--text) !important;
  border-left: 4px solid var(--accent) !important;
}
[data-testid="stAlert"] p,
[data-testid="stAlert"] span {
  color: var(--text) !important;
}

/* ── MOLTIPLICATORE PROGRESSIVO SCHEDINA ─────────────────── */
.mult-box {
  background: linear-gradient(135deg, #0d1f3c, #1a2e4a);
  border: 1px solid var(--accent);
  border-radius: var(--radius);
  padding: 16px 20px;
  margin: 10px 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: var(--glow-blue);
}
.mult-label {
  font-family: 'Syne', sans-serif;
  font-size: 0.75rem;
  color: var(--text2);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}
.mult-value {
  font-family: 'Syne', sans-serif;
  font-size: 2rem;
  font-weight: 800;
  color: var(--gold);
  text-shadow: 0 0 20px rgba(251,191,36,0.3);
}
.mult-prob {
  font-family: 'DM Mono', monospace;
  font-size: 0.85rem;
  color: var(--text2);
}
.mult-vincita {
  font-family: 'DM Mono', monospace;
  font-size: 1rem;
  font-weight: 600;
  color: var(--green);
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# ⚙️ CONFIGURAZIONE GLOBALE
# ==========================================
# ── Caricamento sicuro della API Key ──────────────────────────────────────────
# Priorità: 1) st.secrets (Streamlit Cloud)  2) variabile d'ambiente / .env locale

# Stagione dinamica: le leghe europee usano l'anno di inizio stagione.
# Agosto-dicembre → stagione = anno corrente (es. agosto 2026 → "2026")
# Gennaio-luglio  → stagione = anno precedente (es. marzo 2026 → "2025")
_oggi = datetime.now()
STAGIONE = str(_oggi.year) if _oggi.month >= 8 else str(_oggi.year - 1)
from matrix_leghe import (
    XG_MAX, XG_MIN,
    MASTER_LEAGUES, AFFIDABILITA_ORDINE, AFFIDABILITA_BADGE,
    get_affidabilita, LEGHE_ANNO_SOLARE, LEGHE_PLAYOFF, COPPE_EUROPEE, LEGHE_CIECHE,
    COPPE_NAZIONALI,
)
from matrix_api import (
    HEADERS,
    trova_id_multipli, _risolvi_id_per_nome, trova_id_coppa,
    get_active_leagues, analizza_infortuni_pesati_v90,
    scarica_quote_native, analizza_statistiche_stagionali, analizza_statistiche_avanzate_pro,
    analizza_squadra_globale, analizza_h2h_dna_e_andata, trova_lega_squadra,
    rileva_contesto_spareggio, scarica_meteo, scarica_standings_pregressi,
)
from matrix_modello import (
    calcola_tutti_i_mercati, get_quota_finale,
    calcola_edge_pct, kelly_fraction, semplifica_nome,
    costruisci_schedina_dinamica, applica_blend_mercato_1x2, blend_prior_stagione,
)
from matrix_db import (
    salva_schedina, leggi_storico_schedine, aggiorna_esito_schedina,
    controlla_e_aggiorna_risultati, aggiorna_giocata_reale,
)

# ==========================================
# 🕵️ AUTO-DISCOVERY ID LEGA (Risolve Norvegia e altri)
# ==========================================


# Risoluzione runtime ID Norvegia (il problema principale)
_no_leagues = trova_id_multipli("Norway", {"Eliteserien": 69, "Norwegian First Division": 70})
MASTER_LEAGUES["🇳🇴 Eliteserien"]              = _no_leagues.get("Eliteserien", 69)
MASTER_LEAGUES["🇳🇴 1. divisjon (Playoff NO)"] = _no_leagues.get("Norwegian First Division", 70)

# ==========================================
# 🕵️ AUTO-DISCOVERY ID LEGHE SUDAMERICANE/MLS IN COLLISIONE
# ==========================================
# BUGFIX: in MASTER_LEAGUES, "Liga 1 Perù", "División Profesional PY" e "MLS"
# condividevano lo stesso ID hardcoded di un'altra lega non correlata
# (281 = Scottish Prem., 239 = Liga BetPlay, 253 = LigaPro Ecuador),
# causando la sovrapposizione silenziosa dei dati tra le due leghe ogni
# volta che una delle due aveva partite nel periodo selezionato.
# Risolti a runtime cercando per nome all'interno del paese, come già
# fatto sopra per la Norvegia.

MASTER_LEAGUES["🇵🇪 Liga 1 Perù"]             = _risolvi_id_per_nome("Peru", "Liga 1", 281)
MASTER_LEAGUES["🇵🇾 División Profesional PY"] = _risolvi_id_per_nome("Paraguay", "Division Profesional", 239)
MASTER_LEAGUES["🇺🇸 MLS"]                     = _risolvi_id_per_nome("USA", "Major League Soccer", 253)

# ==========================================
# 🏆 AUTO-DISCOVERY COPPE NAZIONALI
# ==========================================
# Le coppe nazionali hanno ID che cambiano ogni stagione su API-Sports.
# Invece di hardcodarli, li troviamo automaticamente per nome+nazione.
# I fallback sono gli ID più comuni osservati storicamente.


# Coppe Nordiche (anno solare)
MASTER_LEAGUES["🇫🇮 Finnish Cup"]            = trova_id_coppa("Finland", "Finnish Cup", 391)
MASTER_LEAGUES["🇳🇴 Norwegian Cup"]          = trova_id_coppa("Norway",  "Norwegian Football Cup", 112)
MASTER_LEAGUES["🇸🇪 Svenska Cupen"]          = trova_id_coppa("Sweden",  "Svenska Cupen", 144)
MASTER_LEAGUES["🇩🇰 DBU Pokalen"]            = trova_id_coppa("Denmark", "DBU Pokalen", 123)

# Coppe Top 5 Europei
MASTER_LEAGUES["🇮🇹 Coppa Italia"]           = trova_id_coppa("Italy",   "Coppa Italia", 137)
MASTER_LEAGUES["🏴󠁧󠁢󠁥󠁮󠁧󠁿 FA Cup"]                = trova_id_coppa("England", "FA Cup", 45)
MASTER_LEAGUES["🏴󠁧󠁢󠁥󠁮󠁧󠁿 EFL Cup"]               = trova_id_coppa("England", "League Cup", 48)
MASTER_LEAGUES["🇪🇸 Copa del Rey"]           = trova_id_coppa("Spain",   "Copa del Rey", 143)
MASTER_LEAGUES["🇩🇪 DFB Pokal"]              = trova_id_coppa("Germany", "DFB Pokal", 81)
MASTER_LEAGUES["🇫🇷 Coupe de France"]        = trova_id_coppa("France",  "Coupe de France", 66)

# Coppe Altri Europei
MASTER_LEAGUES["🇳🇱 KNVB Beker"]             = trova_id_coppa("Netherlands", "KNVB Beker", 90)
MASTER_LEAGUES["🇵🇹 Taça de Portugal"]       = trova_id_coppa("Portugal", "Taça de Portugal", 96)
MASTER_LEAGUES["🇧🇪 Croky Cup"]              = trova_id_coppa("Belgium",  "Belgian Cup", 146)
MASTER_LEAGUES["🇹🇷 Türkiye Kupası"]         = trova_id_coppa("Turkey",   "Türkiye Kupası", 204)
MASTER_LEAGUES["🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Cup"]          = trova_id_coppa("Scotland", "Scottish Cup", 283)
MASTER_LEAGUES["🇨🇭 Schweizer Cup"]          = trova_id_coppa("Switzerland", "Schweizer Cup", 208)
MASTER_LEAGUES["🇦🇹 ÖFB Cup"]               = trova_id_coppa("Austria",  "ÖFB Cup", 219)

# Le coppe nordiche usano anno solare come stagione
LEGHE_ANNO_SOLARE.update({
    "🇫🇮 Finnish Cup", "🇳🇴 Norwegian Cup",
    "🇸🇪 Svenska Cupen", "🇩🇰 DBU Pokalen",
})
# Tutte le coppe sono trattate come coppe (peso momentum 80%, motivazione alta)

# ==========================================
# 📡 MODULI API — DATI GENERALI
# ==========================================







# ==========================================
# 📊 CORE — CALCOLO MERCATI (POISSON)
# ==========================================


# ==========================================
# 💰 QUOTA, VALUE BET, KELLY
# ==========================================



# ==========================================
# 🔎 ANALISI SQUADRA & H2H







# ==========================================
# 🏗️ UTILITY
# ==========================================



# ==========================================
# 🏠 STATO & SIDEBAR
# ==========================================
if 'data_master'     not in st.session_state: st.session_state.data_master     = {}
if 'all_tips_global' not in st.session_state: st.session_state.all_tips_global = []

# ── SIDEBAR HEADER ────────────────────────────────────────────────────────────
st.sidebar.markdown("""
<div class='sidebar-logo'>
  <div class='sidebar-logo-title'>MATRIX BET V90</div>
  <div class='sidebar-logo-sub'>Predictive Analytics Engine</div>
</div>
""", unsafe_allow_html=True)

date_range = st.sidebar.date_input("📅 Periodo di analisi", [])
if len(date_range) == 2:   start_date, end_date = date_range[0], date_range[1]
elif len(date_range) == 1: start_date = end_date = date_range[0]
else:                       start_date = end_date = datetime.now().date()
start_str = start_date.strftime('%Y-%m-%d')
end_str   = end_date.strftime('%Y-%m-%d')

budget_totale = st.sidebar.number_input("💰 Budget (€):", min_value=5.0, value=50.0, step=5.0)

bcol_reset, bcol_scan = st.sidebar.columns(2)
if bcol_reset.button("🗑️ Reset", help="Svuota memoria V90 (hard reset)"):
    st.cache_data.clear()
    st.session_state.data_master     = {}
    st.session_state.all_tips_global = []
    st.sidebar.success("✅ Cache svuotata!")
if bcol_scan.button("🔍 Scansiona", help="Trova campionati attivi nel periodo"):
    with st.spinner("Scansione palinsesto..."):
        st.session_state['active_leagues'] = get_active_leagues(start_date, end_date)

if 'active_leagues' not in st.session_state:
    st.session_state['active_leagues'] = MASTER_LEAGUES
active_dict = st.session_state['active_leagues']
if not active_dict: st.sidebar.warning("Nessun campionato supportato attivo.")

with st.sidebar.expander("🎯 Filtri & Campionati", expanded=False):
    filtro_affidabilita = st.multiselect(
        "Affidabilità dati:",
        ["🟢 ALTA", "🟡 MEDIA", "🔴 BASSA"],
        default=["🟢 ALTA", "🟡 MEDIA", "🔴 BASSA"],
        help="ALTA = standings+stats+infortuni+quote reali. MEDIA = dati buoni con qualche lacuna. "
             "BASSA = fallback pesanti attivi, stime basate su momentum recente."
    )
    livelli_ok = {f.split(" ")[1] for f in filtro_affidabilita}

    leghe_filtrate = {
        k: v for k, v in active_dict.items()
        if get_affidabilita(k) in livelli_ok
    }
    if not leghe_filtrate:
        st.warning("Nessun campionato nel livello di affidabilità selezionato.")

    # Ordina i campionati per affidabilità (Alta prima) poi alfabetico
    leghe_ordinate = sorted(
        leghe_filtrate.keys(),
        key=lambda n: (-AFFIDABILITA_ORDINE.get(get_affidabilita(n), 2), n)
    )

    scelte = st.multiselect("Campionati:", leghe_ordinate, default=leghe_ordinate)

st.sidebar.caption(f"📋 {len(scelte)} campionati selezionati")
btn_genera = st.sidebar.button("⚡ ESTRAI MATRIX V90")

# ==========================================
# ⚡ MOTORE PRINCIPALE
# ==========================================
if btn_genera:
    st.session_state.data_master     = {}
    st.session_state.all_tips_global = []
    now_utc  = datetime.now(timezone.utc)
    tz_ita   = pytz.timezone('Europe/Rome')
    mese_att = datetime.now().month

    tot_leghe = len(scelte)
    barra_progresso = st.progress(0.0, text="Analisi V90 in corso...")

    for idx_lega, name in enumerate(scelte, start=1):
        barra_progresso.progress(
            idx_lega / tot_leghe if tot_leghe else 1.0,
            text=f"Analisi V90: {name} ({idx_lega}/{tot_leghe})")
        f_id         = active_dict[name]
        is_coppa_eu  = name in COPPE_EUROPEE
        is_coppa_naz = name in COPPE_NAZIONALI
        is_coppa     = is_coppa_eu or is_coppa_naz
        is_anno_sol  = name in LEGHE_ANNO_SOLARE
        is_playoff   = name in LEGHE_PLAYOFF
        is_lega_cieca = f_id in LEGHE_CIECHE
        stagione_lega = start_date.year if is_anno_sol else STAGIONE

        # BUGFIX: un errore API su una singola lega (timeout, rate-limit,
        # risposta malformata) non deve piu' interrompere l'estrazione per
        # tutti gli altri campionati selezionati.
        try:
            fix = requests.get(
                "https://v3.football.api-sports.io/fixtures",
                headers=HEADERS,
                params={'league': f_id, 'season': stagione_lega,
                        'from': start_str, 'to': end_str},
                timeout=10
            ).json()
            if not fix.get('response'):
                continue

            # ── STANDINGS ──────────────────────────────────────────
            db_stats: dict = {}
            punti_champions = punti_salvezza = 0
            tot_squadre     = 20
            partite_tot_camp = 38

            std = requests.get(
                "https://v3.football.api-sports.io/standings",
                headers=HEADERS,
                params={'league': f_id, 'season': stagione_lega},
                timeout=10
            ).json()

            if (std.get('response') and len(std['response']) > 0
                    and 'league' in std['response'][0]
                    and 'standings' in std['response'][0]['league']):
                tutti_gironi = std['response'][0]['league']['standings']
                for gruppo in tutti_gironi:
                    tot_squadre      = len(gruppo)
                    partite_tot_camp = max((tot_squadre - 1) * 2, 38)
                    if tot_squadre >= 4:
                        punti_champions = gruppo[3]['points']
                        punti_salvezza  = gruppo[tot_squadre - 4]['points']
                    for t in gruppo:
                        n = semplifica_nome(t['team']['name'])
                        db_stats[n] = {
                            'id':      t['team']['id'],
                            'rank':    t['rank'],
                            'giocate': t['all']['played'],
                            'punti':   t['points'],
                            'ac': (t['home']['goals']['for']     or 0) / max(1, t['home']['played'] or 1),
                            'dc': (t['home']['goals']['against'] or 0) / max(1, t['home']['played'] or 1),
                            'at': (t['away']['goals']['for']     or 0) / max(1, t['away']['played'] or 1),
                            'dt': (t['away']['goals']['against'] or 0) / max(1, t['away']['played'] or 1),
                        }
            else:
                # PLAYOFF RESCUE / STANDINGS FALLBACK
                for f in fix['response']:
                    for tt in ['home', 'away']:
                        n    = semplifica_nome(f['teams'][tt]['name'])
                        t_id = f['teams'][tt]['id']
                        if n not in db_stats:
                            db_stats[n] = {'id': t_id, 'rank': 10, 'giocate': 0,
                                           'punti': 0, 'ac': 0.0, 'dc': 0.0,
                                           'at': 0.0, 'dt': 0.0}

            # ── PRIOR STAGIONE PRECEDENTE ───────────────────────────
            # A inizio stagione (poche 'giocate') le medie gol casa/trasferta
            # sopra sono calcolate su un campione minuscolo (1-2 partite) e
            # sono quindi rumorose. Le si sfuma con le stesse medie della
            # stagione precedente (se disponibile per quella squadra/lega),
            # dando sempre meno peso al dato storico man mano che la
            # stagione corrente accumula partite reali (vedi
            # blend_prior_stagione). Nessun effetto su leghe ad anno solare
            # inter-stagione o su squadre neopromosse (prior assente).
            stats_prev_stagione = scarica_standings_pregressi(f_id, int(stagione_lega) - 1)
            if stats_prev_stagione:
                for n, st_sq in db_stats.items():
                    prev = stats_prev_stagione.get(st_sq['id'])
                    if prev is None:
                        continue
                    giocate_sq = st_sq.get('giocate', 0)
                    for campo in ('ac', 'dc', 'at', 'dt'):
                        st_sq[campo] = blend_prior_stagione(
                            st_sq[campo], prev[campo], giocate_sq)

            # ── CACHE QUOTE ────────────────────────────────────────
            date_giocate = {f['fixture']['date'][:10] for f in fix['response']}
            odds_cache: dict = {}
            for d_match in date_giocate:
                odds_cache[d_match] = scarica_quote_native(f_id, d_match, stagione_lega)

            matches_list = []

            for f in fix['response']:
                if f['fixture']['status']['short'] in ['PST', 'CANC', 'ABD', 'AWD', 'WO']:
                    continue
                fix_id         = f['fixture']['id']
                match_date_str = f['fixture']['date'][:10]
                match_time_utc = datetime.fromisoformat(f['fixture']['date'])
                if match_time_utc <= now_utc: continue
                match_time_ita = match_time_utc.astimezone(tz_ita)
                orario_ita     = match_time_ita.strftime('%d/%m %H:%M')

                c_u = f['teams']['home']['name']
                t_u = f['teams']['away']['name']
                c_s = semplifica_nome(c_u)
                t_s = semplifica_nome(t_u)

                quote_reali_match = odds_cache.get(match_date_str, {}).get(fix_id, {})

                # ── BRANCH CLUB (campionati + playoff) ─────────────
                # Playoff rescue: squadre nei playoff non in classifica principale
                for sn, tid in [(c_s, f['teams']['home']['id']), (t_s, f['teams']['away']['id'])]:
                    if sn not in db_stats:
                        db_stats[sn] = {'id': tid, 'rank': 10, 'giocate': 0, 'punti': 0,
                                        'ac': 0.0, 'dc': 0.0, 'at': 0.0, 'dt': 0.0}

                m_st_c, is_stanca_c, forma_c, m_f_c, rit_c, punti_5_c, punti_prev_5_c, ok_squadra_c = analizza_squadra_globale(db_stats[c_s]['id'])
                m_st_t, is_stanca_t, forma_t, m_f_t, rit_t, punti_5_t, punti_prev_5_t, ok_squadra_t = analizza_squadra_globale(db_stats[t_s]['id'])
                cs_c, fts_c, ok_stag_c = analizza_statistiche_stagionali(f_id, db_stats[c_s]['id'], stagione_lega)
                cs_t, fts_t, ok_stag_t = analizza_statistiche_stagionali(f_id, db_stats[t_s]['id'], stagione_lega)
                # BUGFIX: prima veniva passato il nome-squadra semplificato
                # a wttr.in al posto di una citta' reale (es. "Inter" non e'
                # una citta'); ora si usa la citta' dello stadio dalla fixture,
                # con fallback al vecchio comportamento se assente.
                citta_match = (f['fixture'].get('venue') or {}).get('city') or c_s
                m_met, d_met = scarica_meteo(citta_match)
                (m_h2h_c, m_h2h_t, gol_h2h_c, gol_h2h_t, str_h2h,
                 b_and_c, b_and_t, andata_msg, det_h2h, ok_h2h) = analizza_h2h_dna_e_andata(
                    db_stats[c_s]['id'], db_stats[t_s]['id'])

                # Rilevamento spareggio inter-lega e gara di ritorno
                # BUGFIX: prima venivano passati due volte f_id (la lega della
                # partita), rendendo is_interlega strutturalmente sempre False.
                # Ora si risale alla lega "di casa" di ciascuna squadra per
                # rilevare i veri spareggi promozione/retrocessione tra
                # divisioni diverse.
                lega_c_reale = trova_lega_squadra(db_stats[c_s]['id'], stagione_lega, f_id)
                lega_t_reale = trova_lega_squadra(db_stats[t_s]['id'], stagione_lega, f_id)
                ctx_spar = rileva_contesto_spareggio(
                    fix_id, db_stats[c_s]['id'], db_stats[t_s]['id'],
                    lega_c_reale, lega_t_reale, match_date_str)
                if ctx_spar['is_ritorno'] or ctx_spar['is_interlega']:
                    b_and_c *= ctx_spar['boost_c']
                    b_and_t *= ctx_spar['boost_t']
                    if ctx_spar['msg']:
                        andata_msg = ctx_spar['msg']
                is_interlega = ctx_spar['is_interlega']
                peso_mom_override = ctx_spar['peso_momentum'] if ctx_spar['is_interlega'] else None
                (poss_c, tiri_c, box_c, conv_c, corn_c, cart_c, falli_c,
                 par_c, stile_c, sq_cert_c, gf_10_c, gs_10_c,
                 rig_c, gf_home_c, gs_home_c, gf_away_c, gs_away_c, ok_avz_c) = analizza_statistiche_avanzate_pro(db_stats[c_s]['id'])
                (poss_t, tiri_t, box_t, conv_t, corn_t, cart_t, falli_t,
                 par_t, stile_t, sq_cert_t, gf_10_t, gs_10_t,
                 rig_t, gf_home_t, gs_home_t, gf_away_t, gs_away_t, ok_avz_t) = analizza_statistiche_avanzate_pro(db_stats[t_s]['id'])

                # ── AFFIDABILITÀ DINAMICA (punto 5) ─────────────────────
                # Il badge statico per lega non diceva se, in QUESTA run,
                # una o piu' fonti dati erano cadute in fallback silenzioso
                # (timeout/errore API). Qui contiamo i fallback reali
                # avvenuti per questa specifica partita e degradiamo il
                # livello di affidabilita' mostrato di conseguenza.
                n_degradati = sum(0 if ok else 1 for ok in [
                    ok_squadra_c, ok_squadra_t, ok_stag_c, ok_stag_t,
                    ok_h2h, ok_avz_c, ok_avz_t,
                ])
                _aff_base = get_affidabilita(name)
                if n_degradati >= 4:
                    aff_match = "BASSA"
                elif n_degradati >= 1:
                    _rank = max(1, AFFIDABILITA_ORDINE[_aff_base] - 1)
                    aff_match = {3: "ALTA", 2: "MEDIA", 1: "BASSA"}[_rank]
                else:
                    aff_match = _aff_base

                c_id = db_stats[c_s]['id']; t_id = db_stats[t_s]['id']
                msg_radar = ("⚠️ Radar Infortuni Offline (Lega Minore)" if is_lega_cieca else "")

                if is_lega_cieca:
                    malus_att_c = boost_opp_c = malus_att_t = boost_opp_t = 0.0
                    t1_c=t2_c=t3_c=count_c=sq_c=def_out_c = 0; gk_out_c = False
                    t1_t=t2_t=t3_t=count_t=sq_t=def_out_t = 0; gk_out_t = False
                    if sq_cert_c > 0: sq_c += sq_cert_c; count_c += sq_cert_c; malus_att_c += 0.05*sq_cert_c
                    if sq_cert_t > 0: sq_t += sq_cert_t; count_t += sq_cert_t; malus_att_t += 0.05*sq_cert_t
                else:
                    inj = requests.get("https://v3.football.api-sports.io/injuries",
                                       headers=HEADERS, params={'fixture': fix_id}, timeout=8).json()
                    inf_all = inj.get('response', [])
                    if not isinstance(inf_all, list): inf_all = []
                    if len(inf_all) == 0:
                        ic = requests.get("https://v3.football.api-sports.io/injuries",
                                          headers=HEADERS, params={'team': c_id, 'date': match_date_str}, timeout=8).json()
                        it = requests.get("https://v3.football.api-sports.io/injuries",
                                          headers=HEADERS, params={'team': t_id, 'date': match_date_str}, timeout=8).json()
                        if isinstance(ic.get('response'), list): inf_all.extend(ic['response'])
                        if isinstance(it.get('response'), list): inf_all.extend(it['response'])
                    inf_c = [i for i in inf_all if str(i['team']['id']) == str(c_id)]
                    inf_t = [i for i in inf_all if str(i['team']['id']) == str(t_id)]
                    (malus_att_c, boost_opp_c, t1_c, t2_c, t3_c,
                     count_c, sq_c, gk_out_c, def_out_c) = analizza_infortuni_pesati_v90(inf_c, stagione_lega)
                    (malus_att_t, boost_opp_t, t1_t, t2_t, t3_t,
                     count_t, sq_t, gk_out_t, def_out_t) = analizza_infortuni_pesati_v90(inf_t, stagione_lega)
                    if sq_cert_c > 0 and sq_c == 0: sq_c+=sq_cert_c; count_c+=sq_cert_c; malus_att_c+=0.05*sq_cert_c
                    if sq_cert_t > 0 and sq_t == 0: sq_t+=sq_cert_t; count_t+=sq_cert_t; malus_att_t+=0.05*sq_cert_t

                # Squad Depth Buffer
                if not is_coppa:
                    gap_c = db_stats[c_s].get('punti', 0) - db_stats[t_s].get('punti', 0)
                    gap_t = -gap_c
                    if gap_c >= 15:
                        a = max(0.20, 1.0 - gap_c/45.0); malus_att_c *= a; boost_opp_t *= a
                    elif gap_t >= 15:
                        a = max(0.20, 1.0 - gap_t/45.0); malus_att_t *= a; boost_opp_c *= a

                streak_break_c = (gol_h2h_c == 0) and (count_t > 0 or is_stanca_t)
                streak_break_t = (gol_h2h_t == 0) and (count_c > 0 or is_stanca_c)

                # ── MOTIVAZIONE + PRESSIONE (effetto choking) ─────────────
                m_mot_c = m_mot_t = 1.0
                pressione_c = pressione_t = 0.0
                msg_mot = ""; msg_pressione = ""
                tension_idx = 1.0

                if is_coppa_naz:
                    m_mot_c = m_mot_t = 1.20; tension_idx += 0.25; msg_mot = "🏆 COPPA NAZIONALE"
                elif is_coppa_eu and mese_att in [3, 4, 5]:
                    m_mot_c = m_mot_t = 1.25; tension_idx += 0.3; msg_mot = "🔥 DENTRO O FUORI"
                elif is_coppa_eu:
                    m_mot_c = m_mot_t = 1.15; tension_idx += 0.2; msg_mot = "🇪🇺 Coppa Europea"
                elif is_playoff:
                    m_mot_c = m_mot_t = 1.30; tension_idx += 0.4; msg_mot = "⚡ PLAYOFF"
                elif not is_coppa:
                    punti_c  = db_stats[c_s].get('punti', 0);  punti_t = db_stats[t_s].get('punti', 0)
                    rank_c   = db_stats[c_s].get('rank', 10);  rank_t  = db_stats[t_s].get('rank', 10)
                    gioc_c   = db_stats[c_s].get('giocate', 0); gioc_t = db_stats[t_s].get('giocate', 0)
                    gap_ch_c = punti_champions - punti_c
                    gap_ch_t = punti_champions - punti_t
                    part_rim_c = max(1, partite_tot_camp - gioc_c)
                    part_rim_t = max(1, partite_tot_camp - gioc_t)
                    max_rag_c  = punti_c + part_rim_c * 3
                    max_rag_t  = punti_t + part_rim_t * 3

                    # ── OBIETTIVO CASA ──────────────────────────────
                    if max_rag_c < punti_salvezza:
                        m_mot_c = 0.75; msg_mot += "💀 C.Retrocessa "
                    elif punti_c > punti_salvezza + part_rim_c * 2:
                        m_mot_c = 0.85; msg_mot += "🏖️ C.Salva "
                    elif punti_c >= punti_champions:
                        m_mot_c = 1.20; msg_mot += "🏆 C.InChampions "
                    elif 0 < gap_ch_c <= part_rim_c * 2:
                        urgenza = 1.0 - (gap_ch_c / (part_rim_c * 3))
                        m_mot_c = 1.10 + urgenza * 0.20; msg_mot += "🔥 C.CorsaChamp "
                    elif rank_c >= tot_squadre - 3:
                        m_mot_c = 1.25; msg_mot += "🆘 C.Disperata "
                    elif rank_c >= tot_squadre - 6:
                        m_mot_c = 1.15; msg_mot += "😰 C.ARischio "
                    else:
                        m_mot_c = 1.05

                    # ── OBIETTIVO TRASFERTA ─────────────────────────
                    if max_rag_t < punti_salvezza:
                        m_mot_t = 0.75; msg_mot += "💀 O.Retrocessa"
                    elif punti_t > punti_salvezza + part_rim_t * 2:
                        m_mot_t = 0.85; msg_mot += "🏖️ O.Salva"
                    elif punti_t >= punti_champions:
                        m_mot_t = 1.20; msg_mot += "🏆 O.InChampions"
                    elif 0 < gap_ch_t <= part_rim_t * 2:
                        urgenza = 1.0 - (gap_ch_t / (part_rim_t * 3))
                        m_mot_t = 1.10 + urgenza * 0.20; msg_mot += "🔥 O.CorsaChamp"
                    elif rank_t >= tot_squadre - 3:
                        m_mot_t = 1.25; msg_mot += "🆘 O.Disperata"
                    elif rank_t >= tot_squadre - 6:
                        m_mot_t = 1.15; msg_mot += "😰 O.ARischio"
                    else:
                        m_mot_t = 1.05

                    # ── SCONTRO DIRETTO ─────────────────────────────
                    if abs(rank_c - rank_t) <= 2:
                        tension_idx += 0.25; msg_mot += " ⚔️ScontroDiretto"

                    # ── PRESSIONE CASA (effetto Milan) ──────────────
                    sconf_c = forma_c.count("L")
                    trend_c = punti_5_c - punti_prev_5_c
                    if m_mot_c >= 1.15:  # obiettivo vitale
                        pressione_c += 0.10
                    if sconf_c >= 4:     pressione_c += 0.20
                    elif sconf_c >= 3:   pressione_c += 0.12
                    elif sconf_c >= 2:   pressione_c += 0.06
                    if trend_c <= -6:    pressione_c += 0.10
                    elif trend_c <= -3:  pressione_c += 0.05
                    pressione_c = min(0.35, pressione_c)

                    # ── PRESSIONE TRASFERTA ─────────────────────────
                    sconf_t = forma_t.count("L")
                    trend_t = punti_5_t - punti_prev_5_t
                    if m_mot_t >= 1.15:  pressione_t += 0.10
                    if sconf_t >= 4:     pressione_t += 0.20
                    elif sconf_t >= 3:   pressione_t += 0.12
                    elif sconf_t >= 2:   pressione_t += 0.06
                    if trend_t <= -6:    pressione_t += 0.10
                    elif trend_t <= -3:  pressione_t += 0.05
                    pressione_t = min(0.35, pressione_t)

                    # ── BONUS LIBERTÀ (effetto Cagliari) ───────────
                    if m_mot_c <= 0.90:  # sgombra/retrocessa
                        vitt_c = forma_c.count("W")
                        if vitt_c >= 3: m_mot_c *= 1.12
                        else:           m_mot_c *= 1.05
                    if m_mot_t <= 0.90:
                        vitt_t = forma_t.count("W")
                        if vitt_t >= 3: m_mot_t *= 1.12
                        else:           m_mot_t *= 1.05

                    if pressione_c > 0.15:
                        msg_pressione += f" 😬Pressione Casa:{pressione_c*100:.0f}%"
                    if pressione_t > 0.15:
                        msg_pressione += f" 😬Pressione Osp:{pressione_t*100:.0f}%"

                # Applica pressione ai moltiplicatori
                m_mot_c = m_mot_c * (1 - pressione_c)
                m_mot_t = m_mot_t * (1 - pressione_t)

                # Hybrid xG
                xg_st_c = math.sqrt(max(0.01, db_stats[c_s].get('ac', 0.0)) * max(0.01, db_stats[t_s].get('dt', 0.0)))
                xg_st_t = math.sqrt(max(0.01, db_stats[t_s].get('at', 0.0)) * max(0.01, db_stats[c_s].get('dc', 0.0)))
                # MIGLIORIA 2: xG momentum usa casa/trasferta separati
                # Casa gioca in casa → usiamo i suoi gol_fatti_in_casa vs gol_subiti_in_casa dell'avversario
                xg_mo_c = math.sqrt(max(0.01, gf_home_c) * max(0.01, gs_home_t))
                xg_mo_t = math.sqrt(max(0.01, gf_away_t) * max(0.01, gs_away_c))
                # Peso momentum: inter-lega=100%, coppe/playoff=80%, normale=30%
                if peso_mom_override is not None:
                    peso_mom = peso_mom_override
                elif is_coppa or is_playoff or db_stats[c_s].get('giocate', 0) <= 5:
                    peso_mom = 0.80
                else:
                    peso_mom = 0.30
                peso_std  = 1.0 - peso_mom
                # Stima instabile = il modello sta usando un blend a forte momentum
                # (coppa, playoff, inter-lega o inizio stagione con <=5 partite giocate):
                # su questi casi l'edge dichiarato può gonfiarsi in modo non affidabile
                # (poche partite = xG di momentum molto rumoroso). Usato più sotto per
                # non proporre come "value bet" edge sospetti finché i dati non maturano.
                stima_instabile = peso_mom > 0.30
                xg_base_c = ((xg_st_c * peso_std) + (xg_mo_c * peso_mom)) * m_f_c * m_st_c
                xg_base_t = ((xg_st_t * peso_std) + (xg_mo_t * peso_mom)) * m_f_t * m_st_t

                mal_lega = 0.85 if name in ["🇬🇷 Super League", "🇫🇷 Ligue 1", "🇮🇹 Serie B"] else 1.0
                xg_base_c *= mal_lega; xg_base_t *= mal_lega

                if conv_c < 3.0:   xg_base_c *= 1.15
                elif conv_c > 7.0: xg_base_c *= 0.85
                if conv_t < 3.0:   xg_base_t *= 1.15
                elif conv_t > 7.0: xg_base_t *= 0.85

                xg_base_c *= min(1.20, 1.0 + (box_c/15.0)*0.15)
                xg_base_t *= min(1.20, 1.0 + (box_t/15.0)*0.15)
                xg_base_c *= (1 - min(0.25, (par_c/6.0)*0.20))
                xg_base_t *= (1 - min(0.25, (par_t/6.0)*0.20))

                tot_falli = falli_c + falli_t
                if tot_falli > 28: xg_base_c *= 0.90; xg_base_t *= 0.90
                if fts_c > 35: xg_base_c *= 0.85
                if cs_t  > 35: xg_base_c *= 0.85
                if fts_t > 35: xg_base_t *= 0.85
                if cs_c  > 35: xg_base_t *= 0.85

                # BUGFIX: i tag generati sopra sono "C.Salva"/"O.Salva", non "Sgombra"
                # (refuso di rename mai propagato) — il boost 1.10x non scattava mai.
                sg_c = "C.Salva" in msg_mot; sg_t = "O.Salva" in msg_mot
                xg_c = (xg_base_c * (1-malus_att_c) * (1+boost_opp_t) * m_h2h_c * b_and_c * m_mot_c * (1.10 if sg_t else 1.0))
                xg_t = (xg_base_t * (1-malus_att_t) * (1+boost_opp_c) * m_h2h_t * b_and_t * m_mot_t * (1.10 if sg_c else 1.0))

                msg_streak = ""
                if streak_break_c: xg_c *= 1.45; msg_streak += "🔥 STREAK CASA "
                if streak_break_t: xg_t *= 1.45; msg_streak += "🔥 STREAK OSPITE"
                xg_c *= m_met; xg_t *= m_met

                arb    = f['fixture']['referee'] or "N/D"
                is_sev = any(s in str(arb) for s in ["Orsato","Maresca","Taylor","Oliver","Lahoz","Hernandez"])
                if is_sev: xg_c *= 1.05; xg_t *= 1.05

                # FIX: CAP xG prima di Poisson
                xg_c = min(XG_MAX, max(XG_MIN, xg_c))
                xg_t = min(XG_MAX, max(XG_MIN, xg_t))

                avg_corn = corn_c + corn_t; avg_cart = cart_c + cart_t
                full_tips = calcola_tutti_i_mercati(xg_c, xg_t, avg_corn, avg_cart, is_sev, tot_falli)

                # Blend modello+mercato sul mercato 1X2 (e su tutto cio' che ne
                # deriva: doppie chance, combo con O/U, HT/FT). Nei contesti
                # "instabili" (coppe/playoff/inter-lega/inizio stagione) il
                # modello ha pochi dati e puo' discostarsi molto dal mercato
                # senza una vera ragione (es. un grande favorito valutato ~50%
                # solo per 1-2 partite giocate) — si da' quindi piu' peso al
                # mercato reale (devigato) proprio quando i dati del modello
                # sono meno affidabili. Nessun effetto se le quote reali 1X2
                # non sono disponibili per questa partita.
                peso_mercato_1x2 = 0.55 if stima_instabile else 0.15
                full_tips = applica_blend_mercato_1x2(full_tips, quote_reali_match, peso_mercato_1x2)

                best_key = max(["1","X","2"], key=lambda k: full_tips[k])
                if full_tips[best_key] < 45.0:
                    best_key = "No Segno Fisso"; best_prob = 0.0; best_q = "-"; best_real = False
                else:
                    best_prob = full_tips[best_key]
                    best_q, best_real = get_quota_finale(best_key, best_prob, quote_reali_match)

                SOGLIA_EDGE_SOSPETTO = 60.0  # oltre questa soglia, un edge su dati
                                             # instabili è quasi certamente rumore, non valore reale
                for k, v in full_tips.items():
                    q_fin, is_real = get_quota_finale(k, v, quote_reali_match)
                    edge_v = calcola_edge_pct(v, q_fin)
                    # Nasconde dalle tabelle Value Bet/schedine solo i pick con edge
                    # sospetto su dati ancora instabili (inizio stagione, coppe, playoff).
                    # Non è un taglio permanente: appena la squadra accumula partite
                    # (o non è più in un contesto a momentum forzato) il pick ricompare
                    # regolarmente. La partita resta comunque visibile in "Esplora Partite".
                    if stima_instabile and edge_v > SOGLIA_EDGE_SOSPETTO:
                        continue
                    st.session_state.all_tips_global.append({
                        "Match":  f"{c_u} vs {t_u}", "League": name, "Tip": k,
                        "Prob":   v, "Quota": q_fin, "Real": is_real, "Time": orario_ita,
                        "Edge":   edge_v,
                        "Kelly":  kelly_fraction(v, q_fin),
                        "Aff":    aff_match,
                        "Instabile": stima_instabile,
                        "FixtureID": fix_id,
                    })
                matches_list.append({
                    "orario": orario_ita, "c_u": c_u, "t_u": t_u, "c_s": c_s, "t_s": t_s,
                    "fixture_id": fix_id,
                    "rank_c": db_stats[c_s].get('rank', 10), "rank_t": db_stats[t_s].get('rank', 10),
                    "cs_c": cs_c, "fts_c": fts_c, "cs_t": cs_t, "fts_t": fts_t,
                    "all_tips": full_tips,
                    "best_1x2": (best_key, best_prob, best_q, best_real),
                    "quote_reali": quote_reali_match,
                    "xg_c": xg_c, "xg_t": xg_t, "arb": arb, "is_sev": is_sev,
                    "count_c": count_c, "sq_c": sq_c, "t1_c": t1_c, "t2_c": t2_c,
                    "t3_c": t3_c, "gk_out_c": gk_out_c, "def_out_c": def_out_c,
                    "count_t": count_t, "sq_t": sq_t, "t1_t": t1_t, "t2_t": t2_t,
                    "t3_t": t3_t, "gk_out_t": gk_out_t, "def_out_t": def_out_t,
                    "meteo": d_met, "msg_radar": msg_radar,
                    "dna_h2h": str_h2h, "dettagli_h2h": det_h2h,
                    "streak_msg": msg_streak.strip(), "andata_msg": andata_msg,
                    "msg_mot": msg_mot.strip(),
                    "stan_c": "⚠️ Fatigue" if is_stanca_c else "✅ Riposo",
                    "stan_t": "⚠️ Fatigue" if is_stanca_t else "✅ Riposo",
                    "forma_c": forma_c, "forma_t": forma_t, "rit_c": rit_c, "rit_t": rit_t,
                    "pressione_c": pressione_c, "pressione_t": pressione_t,
                    "msg_pressione": msg_pressione,
                    "poss_c": poss_c, "tiri_c": tiri_c, "conv_c": conv_c, "stile_c": stile_c,
                    "box_c": box_c, "falli_c": falli_c, "parate_c": par_c, "rig_c": rig_c,
                    "gf_home_c": gf_home_c, "gs_home_c": gs_home_c,
                    "poss_t": poss_t, "tiri_t": tiri_t, "conv_t": conv_t, "stile_t": stile_t,
                    "box_t": box_t, "falli_t": falli_t, "parate_t": par_t, "rig_t": rig_t,
                    "gf_away_t": gf_away_t, "gs_away_t": gs_away_t,
                    "corn_tot": avg_corn, "cart_tot": avg_cart, "falli_tot": tot_falli,
                    "aff_dinamica": aff_match, "n_degradati": n_degradati,
                })

            if matches_list:
                st.session_state.data_master[name] = matches_list
        except Exception as e:
            st.warning(f"⚠️ Errore durante l'analisi di **{name}**: {e} — salto questo campionato e continuo con gli altri.")
            continue

    barra_progresso.empty()

# ==========================================
# 🖥️ DISPLAY: 3 TAB
# ==========================================
with st.expander("📊 Storico Schedine", expanded=False):

    if st.button("🔄 Controlla risultati partite finite"):
        with st.spinner("Controllo i risultati reali delle partite..."):
            esito_controllo = controlla_e_aggiorna_risultati()
        st.success(
            f"✅ {esito_controllo['vinte']} vinte, ❌ {esito_controllo['perse']} perse "
            f"aggiornate automaticamente. ⏳ {esito_controllo['ancora_in_attesa']} ancora "
            f"in attesa (partite non finite). 🔍 {esito_controllo['non_valutabili']} da "
            f"verificare a mano (mercato non auto-valutabile o schedina senza fixture ID)."
        )
        st.rerun()

    storico = leggi_storico_schedine(giorni=60)

    if not storico:
        st.warning("Nessuna schedina trovata su Firebase (o la connessione non è "
                   "configurata/raggiungibile — controlla il terminale per eventuali "
                   "errori di connessione).")
        storico_ordinato = []
    else:
        def _data_ordinabile(r):
            """La 'data' e' normalmente 'YYYY-MM-DD' (schedine Matrix/personali),
            ma le bet365 caricate a mano hanno un placeholder 'storico_NN' (date
            esatte non note dagli screenshot) -- che in ordine alfabetico
            finirebbe PRIMA delle date vere, mandando le schedine di oggi in
            fondo. Le riconosciamo e le mandiamo in coda (data fittizia minima)
            cosi' l'ordine resta sempre dalla piu' recente alla piu' vecchia."""
            d = r.get("data", "")
            if len(d) == 10 and d[4] == "-" and d[7] == "-" and d[:4].isdigit():
                return d
            return "0000-00-00"

        storico_ordinato = sorted(
            storico, key=lambda r: (_data_ordinabile(r), r.get("nome", "")), reverse=True)

        def _e_reale(r):
            """True se è una scommessa effettivamente giocata: bet365 caricate
            a mano, salvate dal Carrello come giocata personale, oppure una
            proposta della Matrix che l'utente ha spuntato come 'giocata
            davvero'. False se è solo una proposta automatica mai giocata."""
            return (r.get("fonte") == "bet365_manuale"
                    or str(r.get("nome", "")).startswith("PERSONALE_")
                    or bool(r.get("giocata_reale")))

        storico_reale  = [r for r in storico_ordinato if _e_reale(r)]
        storico_matrix = [r for r in storico_ordinato if not _e_reale(r)]

        def _mostra_metriche(lista, titolo):
            vinte  = sum(1 for r in lista if r.get("esito") == "vinta")
            perse  = sum(1 for r in lista if r.get("esito") == "persa")
            attesa = sum(1 for r in lista if r.get("esito") == "in_attesa")
            concluse = vinte + perse
            st.markdown(f"**{titolo}**")
            c1, c2, c3, c4m = st.columns(4)
            c1.metric("✅ Vinte", vinte)
            c2.metric("❌ Perse", perse)
            c3.metric("⏳ In attesa", attesa)
            c4m.metric("Win rate", f"{(vinte/concluse*100):.1f}%" if concluse else "—")

        mcol1, mcol2 = st.columns(2)
        with mcol1:
            _mostra_metriche(storico_matrix, "🤖 Proposte Matrix (se il modello predice bene)")
        with mcol2:
            _mostra_metriche(storico_reale, "💶 Scommesse reali (soldi effettivamente giocati)")

    st.markdown("---")

    COLORE_ESITO = {"vinta": "#22c55e", "persa": "#ef4444", "in_attesa": "#94a3b8"}
    EMOJI_ESITO  = {"vinta": "✅", "persa": "❌", "in_attesa": "⏳"}

    for r in storico_ordinato:
        esito  = r.get("esito", "in_attesa")
        doc_id = r.get("doc_id")
        selezioni_r = r.get("selezioni", [])

        righe_gambe = []
        n_corrette = 0
        n_valutate = 0
        for s in selezioni_r:
            match_s = s.get('match') or s.get('Match') or '?'
            tip_s   = s.get('tip')   or s.get('Tip')   or '?'
            eg = s.get('esito_gamba')
            if eg in ("vinta", "persa"):
                n_valutate += 1
                if eg == "vinta":
                    n_corrette += 1
                icona_gamba = "✅" if eg == "vinta" else "❌"
            else:
                icona_gamba = "⏳"
            righe_gambe.append(f"{icona_gamba} {match_s} → {tip_s}")
        legs_txt = "<br>".join(righe_gambe)

        conteggio_txt = f" · {n_corrette}/{n_valutate} corrette" if n_valutate else ""

        tag = "💶 Reale" if _e_reale(r) else "🤖 Matrix"
        quota_tot = r.get('quota_totale') or 0
        label = (f"{EMOJI_ESITO.get(esito,'⏳')} {r.get('data','?')} — {r.get('nome','?')} "
                 f"· {tag} · quota {quota_tot:.2f}{conteggio_txt}")

        is_fonte_reale = (r.get("fonte") == "bet365_manuale"
                           or str(r.get("nome", "")).startswith("PERSONALE_"))

        with st.expander(label, expanded=False):
            st.markdown(f"""
<div style="font-size:0.85rem;color:var(--text2);">{legs_txt or '—'}</div>
<div style="font-size:0.78rem;color:var(--text2);margin-top:4px;">
    Quota tot: {quota_tot:.2f} · Prob. dichiarata: {(r.get('probabilita_congiunta') or 0)*100:.1f}% ·
    Budget: {r.get('budget',0):.2f}€
</div>
""", unsafe_allow_html=True)

            if not is_fonte_reale and doc_id:
                giocata_attuale = bool(r.get("giocata_reale"))
                giocata_nuova = st.checkbox(
                    "💶 L'ho giocata davvero (conta anche nelle statistiche reali)",
                    value=giocata_attuale, key=f"giocata_{doc_id}")
                if giocata_nuova != giocata_attuale:
                    if aggiorna_giocata_reale(doc_id, giocata_nuova):
                        st.rerun()
                    else:
                        st.error("Errore nel salvataggio — controlla il terminale.")

            if esito == "in_attesa" and doc_id:
                bcol1, bcol2, _ = st.columns([1, 1, 4])
                if bcol1.button("✅ Vinta", key=f"vinta_{doc_id}"):
                    if aggiorna_esito_schedina(doc_id, "vinta"):
                        st.rerun()
                    else:
                        st.error("Errore nel salvataggio — controlla il terminale.")
                if bcol2.button("❌ Persa", key=f"persa_{doc_id}"):
                    if aggiorna_esito_schedina(doc_id, "persa"):
                        st.rerun()
                    else:
                        st.error("Errore nel salvataggio — controlla il terminale.")

st.markdown("---")

if st.session_state.data_master:
    t1, t2, t3 = st.tabs(["🛒 TOP 10 & BUILDER", "🔬 ESPLORATORE PARTITE", "🏆 SCHEDINE AUTOMATICHE"])

    # ─── TAB 1 ──────────────────────────────────────────────────────────────────
    with t1:
        st.header("🛒 BET BUILDER & CLASSIFICHE OMNI-MARKET")
        st.caption("💡 Edge% = valore atteso · Kelly% = puntata suggerita (su quote basse può dare 0%).")

        def mostra_tabella(titolo, tip_filter, min_q=1.01, max_q=99.0, max_rows=10, sort_by="Edge", solo_kelly_positivo=True):
            st.subheader(titolo)
            pool = [x for x in st.session_state.all_tips_global
                    if (tip_filter(x['Tip']) if callable(tip_filter) else x['Tip'] in tip_filter)
                    and float(x['Quota']) >= min_q
                    and float(x['Quota']) <= max_q
                    and (float(x.get('Edge', 0)) > 0 if solo_kelly_positivo else True)]
            if not pool:
                st.info("Nessun dato per questa categoria.")
                return []
            df = pd.DataFrame(pool).sort_values(sort_by, ascending=False).head(max_rows).copy()
            cols = ['Match','Tip','Prob','Quota','Edge','Kelly','Time','League','Aff','FixtureID']
            df = df[cols].copy()   # .copy() evita che la modifica di Kelly corrompa all_tips_global
            df['Kelly'] = (df['Kelly'] * 100).round(1)
            # Colonna Affidabilità: badge visivo, calcolato per-partita in QUESTA
            # run (aff_match) invece che dalla sola classificazione statica per lega.
            df['Aff'] = df['Aff'].apply(lambda a: AFFIDABILITA_BADGE[a][0])
            df.insert(0, "🛒", False)
            ed = st.data_editor(df,
                column_config={
                    "🛒":    st.column_config.CheckboxColumn("Seleziona", default=False),
                    "Prob":  st.column_config.NumberColumn("Probabilità (%)", format="%.1f%%"),
                    "Quota": st.column_config.NumberColumn("Quota",           format="%.2f"),
                    "Edge":  st.column_config.NumberColumn("Edge (%)",        format="%.1f%%"),
                    "Kelly": st.column_config.NumberColumn("Kelly (%)",        format="%.1f%%"),
                    "Aff":   st.column_config.TextColumn("Dati", help="🟢 Alta 🟡 Media 🔴 Bassa affidabilità"),
                },
                # FixtureID resta nei dati ma non si vede in tabella: serve solo
                # per il controllo automatico dei risultati (Storico Schedine).
                column_order=['🛒','Match','Tip','Prob','Quota','Edge','Kelly','Time','League','Aff'],
                hide_index=True, use_container_width=True,
                disabled=['Match','Tip','Prob','Quota','Edge','Kelly','Time','League','Aff','FixtureID'],
                key=f"ed_{titolo}")
            return ed[ed["🛒"] == True].to_dict('records')

        # Score combinato per Top Assoluta: bilancia probabilità alta e edge positivo
        for tip in st.session_state.all_tips_global:
            tip['Score'] = (tip['Prob'] / 100.0) * max(0, tip['Edge']) if tip['Edge'] > 0 else 0.0

        sel_1  = mostra_tabella("👑 Top 10 Value Bet Assoluta (1.05–1.50)",
                                lambda t: t not in ["U4.5","Casa O0.5","Ospite O0.5"],
                                min_q=1.10, max_q=1.50, sort_by="Score")
        sel_2  = mostra_tabella("🛡️ Top 10 Doppie Chance (1.05–1.80)",
                                ["1X","X2","12"],
                                min_q=1.10, max_q=1.80, sort_by="Score")
        sel_3  = mostra_tabella("⚽ Top 10 Over / Under (1.05–2.00)",
                                lambda t: (t.startswith("O") or t.startswith("U")) and "+" not in t,
                                min_q=1.10, max_q=2.00, sort_by="Score")
        sel_4  = mostra_tabella("🎯 Top 10 Goal / NoGoal (1.05–2.00)",
                                ["Goal","NoGoal"],
                                min_q=1.10, max_q=2.00, sort_by="Score")
        sel_mg = mostra_tabella("🥅 Top 10 Multigol (1.05–2.00)",
                                lambda t: t.startswith("MG"),
                                min_q=1.10, max_q=2.00, sort_by="Score")
        sel_co = mostra_tabella("🧩 Top 10 Combo Match (1.05–2.50)",
                                lambda t: "+" in t,
                                min_q=1.10, max_q=2.50, sort_by="Score")
        sel_6  = mostra_tabella("🧨 Top 10 Azzardi (Quote 2.50–5.00)",
                                lambda t: True,
                                min_q=2.50, max_q=5.00, sort_by="Edge", solo_kelly_positivo=False)

        tutte = (sel_1 + sel_2 + sel_3 + sel_4 + sel_mg + sel_co + sel_6
                 + list(st.session_state.get("carrello_extra", {}).values()))
        viste: set = set(); carrello = []
        for item in tutte:
            k = f"{item['Match']}_{item['Tip']}"
            if k not in viste: viste.add(k); carrello.append(item)

        st.markdown("---")
        st.markdown("<div class='strategy-box builder-bg'>", unsafe_allow_html=True)
        st.header("🧾 IL TUO CARRELLO")
        if carrello:
            q_tot_b = prob_tot_b = 1.0
            txt = "=== RICEVUTA MATRIX V90 ===\n\n"
            for pick in carrello:
                edge = pick.get('Edge', 0); kelly = pick.get('Kelly', 0)
                bc   = "quota-real" if pick.get('Real') else "quota-calc"
                ec_c = "edge-positive" if edge > 0 else "edge-negative"
                st.markdown(
                    f"<div class='schedina-row'>"
                    f"<div><div style='font-weight:600;color:var(--text);'>✅ {pick['Match']} → <strong>{pick['Tip']}</strong></div>"
                    f"<div class='schedina-match'>{pick.get('League','')} | {pick['Time']}</div></div>"
                    f"<div style='text-align:right;'>"
                    f"<span class='{bc}'>Q {pick['Quota']:.2f}</span> "
                    f"<span class='{ec_c}'>{edge:+.1f}%</span> "
                    f"<span class='kelly-pill'>K: {kelly*100:.1f}%</span>"
                    f"</div></div>",
                    unsafe_allow_html=True)
                q_tot_b    *= float(pick['Quota'])
                prob_tot_b *= float(pick['Prob']) / 100.0
                txt += f"[{pick['Time']}] {pick['Match']} -> {pick['Tip']} @ {pick['Quota']:.2f} | Edge: {edge:.1f}%\n"
            txt += (f"\n📊 QUOTA TOTALE: {q_tot_b:.2f}\n"
                    f"🎯 PROBABILITÀ CONGIUNTA: {prob_tot_b*100:.2f}%\n"
                    f"💰 VINCITA STIMATA (su {budget_totale}€): ~{budget_totale*q_tot_b:.2f}€\n")
            cb1, cb2, cb3 = st.columns(3)
            cb1.metric("Quota Totale",          f"{q_tot_b:.2f}")
            cb2.metric("Prob. Congiunta",       f"{prob_tot_b*100:.2f}%")
            cb3.metric(f"Vincita ({budget_totale}€)", f"~{budget_totale*q_tot_b:.2f}€")
            st.download_button("💾 SCARICA SCHEDINA (TXT)", data=txt,
                               file_name=f"Matrix_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                               mime="text/plain")

            st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
            stake_personale = st.number_input(
                "Quanto punti su questa schedina (€):", min_value=0.5, value=10.0,
                step=0.5, key="stake_personale_input")
            if st.button("🗂️ Salva questa schedina come giocata personale"):
                nome_personale = f"PERSONALE_{datetime.now().strftime('%H%M%S')}"
                if salva_schedina(nome_personale, _oggi.strftime("%Y-%m-%d"),
                                   carrello, q_tot_b, prob_tot_b, stake_personale):
                    st.success("✅ Salvata! La trovi nello Storico Schedine in cima alla pagina.")
                    st.rerun()
                else:
                    st.error("❌ Errore nel salvataggio — controlla il terminale per il dettaglio.")
        else:
            st.info("👆 Spunta qualche voce dalle classifiche per costruire la schedina.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ─── TAB 2 ──────────────────────────────────────────────────────────────────
    with t2:
        st.write(f"Partite per il periodo **{start_str} / {end_str}**.")
        for camp, matches in st.session_state.data_master.items():
            # Affidabilità dinamica: il peggior livello osservato tra le
            # partite di questa lega in QUESTA run — non solo la
            # classificazione statica — così un fallback API temporaneo
            # si vede subito invece di restare nascosto dietro un 🟢.
            aff = min((m.get('aff_dinamica', get_affidabilita(camp)) for m in matches),
                      key=lambda a: AFFIDABILITA_ORDINE.get(a, 2), default=get_affidabilita(camp))
            n_degr_lega = sum(1 for m in matches if m.get('n_degradati', 0) > 0)
            aff_icon, aff_color, aff_desc = AFFIDABILITA_BADGE[aff]
            with st.expander(f"🏆 {camp}  {aff_icon}", expanded=False):
                st.markdown(
                    f"<span class='tag' style='background:{aff_color}22;border:1px solid {aff_color}55;"
                    f"color:{aff_color} !important;'>{aff_icon} Affidabilità {aff} — {aff_desc}</span>",
                    unsafe_allow_html=True)
                if n_degr_lega > 0:
                    st.caption(f"⚠️ {n_degr_lega}/{len(matches)} partite con almeno una fonte dati "
                               f"caduta in fallback in questa sessione (vedi ⚠️ nel titolo).")
                for m in sorted(matches, key=lambda x: x['orario']):
                    _degr_tag = " ⚠️" if m.get('n_degradati', 0) > 0 else ""
                    titolo_e = (f"🕒 {m['orario']} | 🏟️ {m['c_u']} vs {m['t_u']} | "
                                f"👑 {m['best_1x2'][0]}{_degr_tag}"
                                if m['best_1x2'][0] != "No Segno Fisso"
                                else f"🕒 {m['orario']} | 🏟️ {m['c_u']} vs {m['t_u']} | ⚠️ No Bet{_degr_tag}")
                    with st.expander(titolo_e, expanded=False):

                        st.markdown(
                            f"<div style='font-size:0.85em;color:#7f8c8d;margin-bottom:10px;'>"
                            f"<b>Arbitro:</b> {m['arb']} | "
                            f"<b>VAR:</b> {'⚠️ Fiscale' if m['is_sev'] else '⚖️ Standard'} | "
                            f"<b>Clima:</b> {m['meteo']}</div>", unsafe_allow_html=True)

                        if m.get('msg_radar'): st.warning(m['msg_radar'])
                        tags = ""
                        if m['msg_mot']:    tags += f"<span class='tag tag-giallo'>{m['msg_mot']}</span> "
                        if m.get('msg_pressione'): tags += f"<span class='tag tag-rosso'>{m['msg_pressione'].strip()}</span> "
                        if m['andata_msg']: tags += f"<span class='tag tag-blu'>{m['andata_msg']}</span> "
                        if m['streak_msg']: tags += f"<span class='tag tag-rosso'>{m['streak_msg']}</span> "
                        if tags: st.markdown(f"<div style='margin-bottom:15px;'>{tags}</div>", unsafe_allow_html=True)

                        st.markdown("### 🎯 PREVISIONI MATRIX V90")
                        pc1, pc2 = st.columns([1, 1.5])
                        with pc1:
                            if m['best_1x2'][0] == "No Segno Fisso":
                                st.markdown("""
<div class="pick-card" style="border-color:#3d1515;">
  <div style="font-size:2rem;margin:8px 0;">⚠️</div>
  <div style="font-family:'Syne',sans-serif;font-weight:700;color:#f87171;">NESSUN SEGNO SICURO</div>
  <div style="font-size:0.8rem;color:var(--text2);margin-top:8px;">Usa Combo o Multigol</div>
</div>""", unsafe_allow_html=True)
                            else:
                                bc  = "quota-real" if m['best_1x2'][3] else "quota-calc"
                                bl  = "Bet365" if m['best_1x2'][3] else "V90 Est."
                                edge_v  = calcola_edge_pct(m['best_1x2'][1], float(m['best_1x2'][2]))
                                kelly_v = kelly_fraction(m['best_1x2'][1], float(m['best_1x2'][2]))
                                ec_cls  = "edge-positive" if edge_v > 0 else "edge-negative"
                                st.markdown(f"""
<div class="pick-card">
  <div style="font-size:0.75rem;color:var(--text2);text-transform:uppercase;letter-spacing:0.1em;">👑 Miglior Segno</div>
  <div class="pick-sign">{m['best_1x2'][0]}</div>
  <div class="pick-prob">Probabilità stimata: <strong style="color:var(--text)">{m['best_1x2'][1]:.1f}%</strong></div>
  <div style="margin-bottom:10px;">
    <span class="{ec_cls}">Edge {edge_v:+.1f}%</span>
    <span class="kelly-pill">Kelly {kelly_v*100:.1f}%</span>
  </div>
  <div><span class="{bc}">{bl}: {m['best_1x2'][2]}</span></div>
</div>""", unsafe_allow_html=True)
                        with pc2:
                            excl = ["U4.5","O0.5","O1.5","Casa O0.5","Ospite O0.5"]
                            top3 = sorted({k:v for k,v in m['all_tips'].items() if k not in excl}.items(),
                                          key=lambda x: x[1], reverse=True)[:3]
                            rows = ""
                            top3_dettagli = []
                            for idx, (tk, tv) in enumerate(top3):
                                qf, qreal = get_quota_finale(tk, tv, m['quote_reali'])
                                ef    = calcola_edge_pct(tv, qf)
                                ec_c  = "edge-positive" if ef > 0 else "edge-negative"
                                qc    = "quota-real" if qreal else "quota-calc"
                                medal = ["🥇","🥈","🥉"][idx]
                                rows += (f"<div class='top3-row'>"
                                         f"<span>{medal} <span class='top3-tip'>{tk}</span>"
                                         f"<span class='top3-prob' style='margin-left:6px;'>{tv:.0f}%</span></span>"
                                         f"<span><span class='{ec_c}'>{ef:+.0f}%</span> "
                                         f"<span class='{qc}' style='margin-left:4px;'>Q{qf}</span></span></div>")
                                top3_dettagli.append({"tip": tk, "prob": tv, "quota": qf,
                                                       "real": qreal, "edge": ef, "medal": medal})
                            st.markdown(
                                f"<div class='top3-card'>"
                                f"<div class='section-header' style='margin-bottom:12px;'>"
                                f"<span style='font-family:Syne,sans-serif;font-weight:700;font-size:0.9rem;'>🔝 TOP 3 OMNI-MARKET</span></div>"
                                f"{rows}</div>", unsafe_allow_html=True)

                        # ── Aggiungi al carrello direttamente da qui ────────────
                        # Le selezioni finiscono nello stesso "carrello_extra"
                        # condiviso col Tab 1 (Top 10 & Builder) -- compaiono
                        # sempre nella sezione "IL TUO CARRELLO" li', da dove si
                        # possono salvare come giocata personale.
                        st.session_state.setdefault("carrello_extra", {})
                        match_str = f"{m['c_u']} vs {m['t_u']}"
                        candidati_carrello = []
                        if m['best_1x2'][0] != "No Segno Fisso":
                            candidati_carrello.append({
                                "label": f"👑 {m['best_1x2'][0]} (Q {m['best_1x2'][2]})",
                                "Match": match_str, "Tip": m['best_1x2'][0],
                                "Prob": m['best_1x2'][1], "Quota": m['best_1x2'][2],
                                "Real": m['best_1x2'][3],
                                "Edge": calcola_edge_pct(m['best_1x2'][1], float(m['best_1x2'][2])),
                                "Kelly": kelly_fraction(m['best_1x2'][1], float(m['best_1x2'][2])),
                            })
                        for d in top3_dettagli:
                            candidati_carrello.append({
                                "label": f"{d['medal']} {d['tip']} (Q {d['quota']})",
                                "Match": match_str, "Tip": d["tip"],
                                "Prob": d["prob"], "Quota": d["quota"], "Real": d["real"],
                                "Edge": d["edge"], "Kelly": kelly_fraction(d["prob"], float(d["quota"])),
                            })

                        if candidati_carrello:
                            st.markdown("**➕ Aggiungi alle mie schedine:**")
                            cols_add = st.columns(len(candidati_carrello))
                            carrello_extra_cambiato = False
                            for col_add, cand in zip(cols_add, candidati_carrello):
                                k_carrello = f"{match_str}_{cand['Tip']}"
                                gia_presente = k_carrello in st.session_state.carrello_extra
                                checked = col_add.checkbox(
                                    cand["label"], value=gia_presente,
                                    key=f"chk_t2_{m['fixture_id']}_{cand['Tip']}")
                                if checked and not gia_presente:
                                    st.session_state.carrello_extra[k_carrello] = {
                                        **cand, "League": camp, "Time": m['orario'],
                                        "FixtureID": m['fixture_id'],
                                    }
                                    carrello_extra_cambiato = True
                                elif not checked and gia_presente:
                                    st.session_state.carrello_extra.pop(k_carrello, None)
                                    carrello_extra_cambiato = True
                            if carrello_extra_cambiato:
                                # Il Tab 1 (dove vive il Carrello) è già stato eseguito
                                # prima di questo punto nello stesso giro dello script:
                                # serve un rerun immediato perché la nuova selezione
                                # compaia subito nel Carrello invece che al giro dopo.
                                st.rerun()

                        st.markdown("---")
                        st.markdown("### 📊 CONFRONTO FORZE IN CAMPO")
                        ch, cvs, ca = st.columns([4, 1, 4])

                        def scheda(col, nome, rank, xg, forma, stan, count, t1_s, sq,
                                   gk_out, def_out, stile, poss, par, conv, cs, fts, colore, icona):
                            with col:
                                panel_cls = "team-panel-home" if icona == "🏠" else "team-panel-away"
                                xg_cls    = "xg-home"        if icona == "🏠" else "xg-away"
                                rank_lbl  = "" if camp in COPPE_EUROPEE \
                                            else f'<span style="font-size:0.7rem;color:var(--text2);margin-left:6px;">#{rank}</span>'
                                forma_html = ""
                                for ch in (forma or ""):
                                    fc = "form-W" if ch=="W" else ("form-D" if ch=="D" else "form-L")
                                    forma_html += f'<span class="form-char {fc}">{ch}</span>'
                                badge_assenti = ""
                                if t1_s > 0:  badge_assenti += f'<span class="tag tag-rosso">⭐ {t1_s} Star out</span>'
                                if sq > 0:    badge_assenti += f'<span class="tag tag-rosso">🟥 {sq} Squalif.</span>'
                                if gk_out:    badge_assenti += '<span class="tag tag-rosso">🧤 PO out</span>'
                                if def_out>=2: badge_assenti += '<span class="tag tag-rosso">🧱 2+ Dif. out</span>'
                                xg_pct = min(100, int((xg / 3.2) * 100))
                                bar_cls = "xg-bar-home" if icona == "🏠" else "xg-bar-away"
                                fatica = "⚠️ Fatigue" if "Fatigue" in stan else "✅ Riposo"
                                st.markdown(f"""
<div class="team-panel {panel_cls}">
  <div class="team-panel-shine"></div>
  <div class="team-name">{icona} {nome} {rank_lbl}</div>
  <div class="{xg_cls} xg-number">xG {xg:.2f}</div>
  <div class="xg-bar-wrap"><div class="xg-bar-fill {bar_cls}" style="width:{xg_pct}%"></div></div>
  <div style="margin-bottom:8px;">{forma_html}<span style="font-size:0.72rem;color:var(--text2);margin-left:8px;">{fatica}</span></div>
  <div style="margin-bottom:10px;">{badge_assenti if badge_assenti else f'<span class="tag tag-verde">✅ Rosa al completo</span>' if count==0 else f'<span class="tag tag-giallo">🚑 {count} assenti</span>'}</div>
  <div class="divider"></div>
  <div class="stat-row"><span class="stat-label">Stile di gioco</span><span class="stat-value">{stile}</span></div>
  <div class="stat-row"><span class="stat-label">Possesso medio</span><span class="stat-value">{poss:.0f}%</span></div>
  <div class="stat-row"><span class="stat-label">Parate / gara</span><span class="stat-value">{par:.1f}</span></div>
  <div class="stat-row"><span class="stat-label">Cinismo (da gioco)</span><span class="stat-value">1 gol / {conv:.1f} tiri</span></div>
  <div class="stat-row"><span class="stat-label">Clean Sheet</span><span class="stat-value" style="color:var(--green)">{cs:.0f}%</span></div>
  <div class="stat-row" style="border:none"><span class="stat-label">A Secco</span><span class="stat-value" style="color:var(--red)">{fts:.0f}%</span></div>
</div>""", unsafe_allow_html=True)


                        scheda(ch, m['c_s'], m['rank_c'], m['xg_c'], m['forma_c'], m['stan_c'],
                               m['count_c'], m['t1_c'], m['sq_c'], m['gk_out_c'], m['def_out_c'],
                               m['stile_c'], m['poss_c'], m['parate_c'], m['conv_c'],
                               m['cs_c'], m['fts_c'], "#2980b9", "🏠")
                        with cvs:
                            st.markdown("<div class='vs-badge'>VS</div>", unsafe_allow_html=True)
                        scheda(ca, m['t_s'], m['rank_t'], m['xg_t'], m['forma_t'], m['stan_t'],
                               m['count_t'], m['t1_t'], m['sq_t'], m['gk_out_t'], m['def_out_t'],
                               m['stile_t'], m['poss_t'], m['parate_t'], m['conv_t'],
                               m['cs_t'], m['fts_t'], "#e74c3c", "✈️")

                        st.markdown("---")
                        b1, b2 = st.columns([1, 1.5])
                        with b1:
                            st.markdown("**Metriche Gara**")
                            st.markdown(f"🚩 Corner: **{m['corn_tot']:.1f}** | "
                                        f"🟨 Cartellini: **{m['cart_tot']:.1f}** | "
                                        f"🛑 Falli: **{m['falli_tot']:.1f}**")
                        with b2:
                            st.markdown("**Ritardi & Storico**")
                            def render_ritardi(rit_list, label):
                                if not rit_list:
                                    st.markdown(f"**{label}:** <span style='color:var(--green);font-size:0.85em;'>✅ Nessun ritardo significativo</span>", unsafe_allow_html=True)
                                else:
                                    pills = " ".join([f"<span class='tag tag-{'rosso' if r['peso']>=2.5 else 'giallo' if r['peso']>=1.5 else 'verde'}'>{r['label']}</span>" for r in rit_list])
                                    st.markdown(f"**{label}:** {pills}", unsafe_allow_html=True)
                            render_ritardi(m['rit_c'], "Ritardi Casa")
                            render_ritardi(m['rit_t'], "Ritardi Ospite")
                            st.markdown(f"**DNA:** <span class='dna-testo'>{m['dna_h2h']}</span>",
                                        unsafe_allow_html=True)
                            if m['dettagli_h2h']:
                                with st.expander("🔍 Ultimi 5 Scontri Diretti"):
                                    st.markdown(f"<div class='h2h-box'>{m['dettagli_h2h']}</div>",
                                                unsafe_allow_html=True)

    # ─── TAB 3 ──────────────────────────────────────────────────────────────────
    with t3:
        st.header("🏆 Generatore Automatico Ottimizzato V90")
        st.caption("💡 Budget per fascia allocato con Kelly Criterion (8% frazionato).")

        if len(st.session_state.all_tips_global) >= 4:
            testo_export = f"=== MATRIX V90: SCHEDINE ===\nPeriodo: {start_str}/{end_str}\n\n"

            # Allocazione dinamica Kelly per fascia
            kp = st.session_state.all_tips_global

            # Allocazione fissa 60/30/10 — stabile e prevedibile.
            # Il Kelly viene usato solo per la puntata suggerita per scommessa,
            # non per determinare il budget di fascia (troppo volatile sulle quote basse).
            bud_s = budget_totale * 0.60
            bud_p = budget_totale * 0.30
            bud_a = budget_totale * 0.10

            # Config schedine: (titolo, emoji, cls, colore_header, colore_accent)
            SCHEDINE_CFG = [
                ("SAFETY",      "🟢", "safety-bg",      "#0a1f0f", "#22c55e",
                 "Solo scommesse con edge > 0%, quota 1.12–1.50."),
                ("PERFORMANCE", "🟠", "performance-bg", "#1f140a", "#f59e0b",
                 "Quote medie, max un evento per partita."),
                ("AZZARDO",     "🔴", "risk-bg",        "#1f0a0a", "#ef4444",
                 "Quote alte — max 10% del capitale."),
            ]
            SCHEDINE_PARAMS = [
                # campi: pool, min_q, max_q, target_mult, max_match_q, (inutilizzato),
                # budget, max_righe, ordina_per, min_prob, max_prob.
                # Safety: torna alla composizione FLESSIBILE (ordina_per="edge",
                # come Performance/Azzardo) invece della ricerca a numero fisso
                # di gambe ("prob_range"). Quest'ultima richiedeva un numero
                # ESATTO di selezioni (2) nella fascia di quota 1.12-1.50: nei
                # giorni con poche partite idonee (anche solo 1) non trovava mai
                # nulla e la Safety spariva del tutto. Con la modalita' flessibile
                # accumula le migliori selezioni per edge fino a un massimo di 3
                # gambe, fermandosi al raggiungimento del target di quota — quindi
                # propone sempre qualcosa quando c'e' almeno una selezione valida.
                # Include anche i mercati Over/Goal nel pool (in precedenza esclusi):
                # nei giorni con molte partite di coppa erano quasi le uniche voci
                # a edge positivo, ed escluderle lasciava la Safety senza abbastanza
                # selezioni per completare la combo.
                (pool_s := kp,
                 1.12, 1.50, 2.0,  2.0,  set(),  bud_s, 3, "edge",
                 None, None),
                (kp,   1.51, 2.20, 5.0,  2.20, None,  bud_p, 12, "edge", None, None),
                (kp,   2.21, 4.50, 30.0, 4.50, None,  bud_a, 12, "edge", None, None),
            ]

            escludi_prev = set()
            for idx, (nome, emoji, cls, bg_col, acc_col, nota) in enumerate(SCHEDINE_CFG):
                (pool_f, min_q, max_q, target, mq, _, budget, max_righe_f,
                 ordina_per_f, min_prob_f, max_prob_f) = SCHEDINE_PARAMS[idx]
                escludi = escludi_prev

                slip, q_tot, prob, usate = costruisci_schedina_dinamica(
                    pool_f, min_q, max_q, target, escludi_match=escludi, max_match_q=mq,
                    max_righe=max_righe_f, ordina_per=ordina_per_f,
                    min_prob_congiunta=min_prob_f, max_prob_congiunta=max_prob_f)
                escludi_prev = usate
                vincita_tot = budget * q_tot

                # Diagnostica: quante selezioni erano davvero disponibili in
                # questa fascia di quota/edge oggi (a prescindere da quante ne
                # sono poi entrate nella combo) -- utile per capire "perche' solo
                # una gamba" senza dover chiedere ogni volta.
                candidati_f = [x for x in pool_f
                               if min_q <= float(x['Quota']) <= max_q
                               and float(x['Quota']) <= mq
                               and float(x.get('Edge', 0)) > 0
                               and x['Match'] not in escludi]
                n_candidati = len(candidati_f)
                n_match_candidati = len({x['Match'] for x in candidati_f})

                # Salva su Firebase la schedina generata (per tracciare nel
                # tempo probabilita' dichiarate vs esiti reali). Fallisce in
                # silenzio se Firebase non e' configurato o raggiungibile --
                # non deve mai bloccare la generazione delle schedine.
                if slip:
                    salva_schedina(nome, _oggi.strftime("%Y-%m-%d"), slip, q_tot, prob, budget)

                # Guardia specifica per Safety: se non ci sono abbastanza selezioni
                # idonee per completare la combo da 2 gambe, salta la schedina
                # invece di proporne una incompleta con l'etichetta "safety".
                if idx == 0 and not slip:
                    motivo_skip = (
                        f"{n_candidati} selezioni idonee disponibili oggi (quota 1.12-1.50, "
                        f"edge positivo) su {n_match_candidati} partite diverse — non bastano "
                        f"per comporre nemmeno una combinazione minima"
                    )
                    st.markdown(f"""
<div class="strategy-box {cls}" style="padding:0;overflow:hidden;">
  <div style="background:linear-gradient(135deg,{bg_col},{bg_col}dd);
    padding:18px 24px;border-bottom:1px solid rgba(255,255,255,0.06);">
    <div style="font-family:'Syne',sans-serif;font-size:1.2rem;font-weight:800;color:{acc_col};">
      {emoji} Schedina {nome}
    </div>
    <div style="font-size:0.75rem;color:var(--text2);margin-top:3px;">{nota}</div>
  </div>
  <div style="padding:16px 24px;color:var(--text2);font-size:0.9rem;">
    Nessuna combinazione trovata oggi ({motivo_skip}) — meglio saltare
    la Safety oggi piuttosto che proporre una combo incompleta.
  </div>
</div>
""", unsafe_allow_html=True)
                    testo_export += f"Schedina {nome}: saltata, {motivo_skip}.\n\n"
                    continue

                txt = f"Schedina {nome} ({budget:.2f}€)\n"

                # Header integrato nel banner
                st.markdown(f"""
<div class="strategy-box {cls}" style="padding:0;overflow:hidden;">
  <div style="background:linear-gradient(135deg,{bg_col},{bg_col}dd);
    padding:18px 24px 14px;border-bottom:1px solid rgba(255,255,255,0.06);">
    <div style="display:flex;align-items:center;justify-content:space-between;">
      <div>
        <div style="font-family:'Syne',sans-serif;font-size:1.2rem;font-weight:800;color:{acc_col};">
          {emoji} Schedina {nome}
        </div>
        <div style="font-size:0.75rem;color:var(--text2);margin-top:3px;">{nota}</div>
        <div style="font-size:0.7rem;color:var(--text2);margin-top:2px;opacity:0.7;">
          ℹ️ {n_candidati} selezioni idonee oggi su {n_match_candidati} partite — usate {len(slip)}
        </div>
      </div>
      <div style="text-align:right;">
        <div style="font-size:0.72rem;color:var(--text2);text-transform:uppercase;letter-spacing:0.08em;">Budget</div>
        <div style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:700;color:var(--text);">
          {budget:.2f}€
        </div>
      </div>
    </div>
  </div>
  <div style="padding:16px 24px;">
""", unsafe_allow_html=True)

                for x in slip:
                    bc     = "quota-real" if x['Real'] else "quota-calc"
                    ed     = x.get('Edge', 0)
                    # Kelly% e puntata calcolati sempre sul budget TOTALE
                    # per essere coerenti con le tabelle Top 10
                    kl     = x.get('Kelly', 0) * 100
                    pt     = budget_totale * x.get('Kelly', 0)
                    ec_cls = "edge-positive" if ed > 0 else "edge-negative"
                    st.markdown(
                        f"<div class='schedina-row'>"
                        f"<div><div style='font-weight:600;color:var(--text);'>"
                        f"<span style='color:var(--orange);font-family:DM Mono,monospace;font-size:0.8rem;'>[{x['Time']}]</span> "
                        f" {x['Match']} → <strong>{x['Tip']}</strong></div>"
                        f"<div class='schedina-match'>{x['League']}</div></div>"
                        f"<div style='text-align:right;white-space:nowrap;'>"
                        f"<span class='{bc}'>Q {x['Quota']}</span> "
                        f"<span class='{ec_cls}'>{ed:+.0f}%</span> "
                        f"<span class='kelly-pill'>{kl:.1f}% → {pt:.2f}€</span>"
                        f"</div></div>",
                        unsafe_allow_html=True)
                    txt += f"  [{x['Time']}] {x['Match']} -> {x['Tip']} @ {x['Quota']:.2f} | Edge:{ed:+.1f}% | Kelly:{kl:.1f}% ({pt:.2f}€)\n"

                # Totale finale compatto dentro il banner
                st.markdown(f"""
    <div style="margin-top:14px;padding:14px 16px;
      background:rgba(255,255,255,0.04);border-radius:var(--radius-sm);
      border:1px solid rgba(255,255,255,0.07);
      display:flex;align-items:center;justify-content:space-between;">
      <div style="display:flex;align-items:center;gap:20px;">
        <div>
          <div style="font-size:0.7rem;color:var(--text2);text-transform:uppercase;letter-spacing:0.08em;">Moltiplicatore</div>
          <div style="font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:800;color:{acc_col};">x{q_tot:.2f}</div>
        </div>
        <div>
          <div style="font-size:0.7rem;color:var(--text2);text-transform:uppercase;letter-spacing:0.08em;">Prob. congiunta</div>
          <div style="font-family:'DM Mono',monospace;font-size:1rem;font-weight:600;color:var(--text);">{prob*100:.1f}%</div>
        </div>
      </div>
      <div style="text-align:right;">
        <div style="font-size:0.7rem;color:var(--text2);text-transform:uppercase;letter-spacing:0.08em;">Vincita stimata</div>
        <div style="font-family:'Syne',sans-serif;font-size:1.4rem;font-weight:800;color:var(--green);">~{vincita_tot:.2f}€</div>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)
                txt += f"Quota:{q_tot:.2f} | Prob:{prob*100:.2f}% | Vincita:~{vincita_tot:.2f}€\n\n"
                testo_export += txt

            st.download_button("💾 SCARICA TUTTE LE 3 SCHEDINE (TXT)",
                               data=testo_export,
                               file_name=f"Matrix_V90_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                               mime="text/plain")
    # ─── TAB 4 ──────────────────────────────────────────────────────────────────
