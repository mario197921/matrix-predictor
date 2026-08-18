import streamlit as st
import requests
import math
import pandas as pd
from datetime import datetime, timezone, timedelta
import pytz
import os
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
def _load_api_key() -> str:
    # Streamlit Cloud: chiave nei Secrets della dashboard
    try:
        key = st.secrets.get("API_KEY_FOOTBALL", "")
        if key:
            return key
    except Exception:
        pass
    # Locale: variabile d'ambiente o file .env
    key = os.getenv("API_KEY_FOOTBALL", "")
    if not key:
        st.error(
            "❌ **API Key non trovata!**\n\n"
            "• **Locale**: crea un file `.env` nella stessa cartella con:\n"
            "  `API_KEY_FOOTBALL=la_tua_chiave`\n\n"
            "• **Streamlit Cloud**: vai su *Settings → Secrets* e aggiungi:\n"
            "  `API_KEY_FOOTBALL = \"la_tua_chiave\"`"
        )
        st.stop()
    return key

API_KEY_FOOTBALL = _load_api_key()
HEADERS          = {'x-apisports-key': API_KEY_FOOTBALL}

# Stagione dinamica: le leghe europee usano l'anno di inizio stagione.
# Agosto-dicembre → stagione = anno corrente (es. agosto 2026 → "2026")
# Gennaio-luglio  → stagione = anno precedente (es. marzo 2026 → "2025")
_oggi = datetime.now()
STAGIONE = str(_oggi.year) if _oggi.month >= 8 else str(_oggi.year - 1)
XG_MAX           = 3.2
XG_MIN           = 0.10
MARGINE_BK       = 0.93   # ~7% margine bookmaker

# ==========================================
# 🗺️ MASTER LEAGUES — ID VERIFICATI E COMPLETI
# ==========================================
# NOTA sugli ID nordici:
#   Eliteserien NOvegese: l'API restituisce ID 69 come alias ma spesso fallisce.
#   La funzione trova_vero_id_lega() lo risolve a runtime interrogando l'endpoint /leagues.
#   Norwegian First Division (playoff): ID 70
#   Allsvenskan Svezia: 113 (verificato stabile)
#   Superettan Svezia (seconda + playoff): 114
#   Veikkausliiga Finlandia: 244
#   Ykkönen Finlandia (seconda + playoff): 245
#   Superliga Danimarca: 119
#   1. Division Danimarca (playoff): 120

MASTER_LEAGUES = {

    # ── COPPE EUROPEE ──────────────────────────────────────────────
    "🇪🇺 Champions League":           2,
    "🇪🇺 Europa League":              3,
    "🇪🇺 Conference League":          848,

    # ── TOP 5 EUROPEI ──────────────────────────────────────────────
    "🇮🇹 Serie A":                    135,
    "🇮🇹 Serie B":                    136,
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League":           39,
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Championship":             40,
    "🇪🇸 La Liga":                    140,
    "🇩🇪 Bundesliga":                 78,
    "🇫🇷 Ligue 1":                    61,

    # ── SECONDE LINEE EUROPEE ──────────────────────────────────────
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 League One":              41,
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 League Two":              42,
    "🇳🇱 Eerste Divisie":             89,
    "🇩🇪 2. Bundesliga":              79,
    "🇪🇸 La Liga 2":                  141,

    # ── ALTRI CAMPIONATI EUROPEI ───────────────────────────────────
    "🇳🇱 Eredivisie":                 88,
    "🇵🇹 Primeira Liga":              94,
    "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Prem.":           281,
    "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Championship":    284,
    "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish League One":      285,
    "🇹🇷 Süper Lig":                  203,
    "🇧🇪 Pro League":                 144,
    "🇬🇷 Super League":               197,
    "🇨🇭 Super League":               207,
    "🇦🇹 Bundesliga":                 218,
    "🇸🇦 Saudi Pro League":           307,

    # ── NORDICI (Anno solare — stagione=anno corrente) ─────────────
    # ID risolti a runtime da trova_vero_id_lega() per Norvegia.
    # Svezia e Finlandia sono stabili.
    "🇳🇴 Eliteserien":               69,   # → auto-discovery runtime
    "🇳🇴 1. divisjon (Playoff NO)":  70,   # Seconda norvegese + playoff promozione
    "🇸🇪 Allsvenskan":               113,
    "🇸🇪 Superettan (Playoff SE)":   114,  # Seconda svedese + playoff
    "🇫🇮 Veikkausliiga":             244,
    "🇫🇮 Ykkönen (Playoff FI)":      245,  # Seconda finlandese + playoff
    "🇩🇰 Superliga":                 119,
    "🇩🇰 1. Division (Playoff DK)":  120,  # Seconda danese + playoff

    # ── SUDAMERICANI ───────────────────────────────────────────────
    "🇧🇷 Brasileirão Série A":       71,
    "🇧🇷 Brasileirão Série B":       72,
    "🇦🇷 Liga Profesional":          128,
    "🇨🇱 Primera División Chile":    265,
    "🇺🇾 Primera División Uruguay":  268,
    "🇨🇴 Liga BetPlay":              239,
    "🇵🇪 Liga 1 Perù":              281,   # NB: verifica ID con auto-discovery
    "🇪🇨 LigaPro Ecuador":          253,
    "🇧🇴 División Profesional":      349,
    "🇵🇾 División Profesional PY":  239,   # NB: verifica ID con auto-discovery
    "🇻🇪 Liga FUTVE":               232,
    "🇲🇽 Liga MX":                  262,
    "🇺🇸 MLS":                      253,
}

# ==========================================
# 🎯 LIVELLO AFFIDABILITÀ DATI
# ==========================================
# Classifica ogni campionato in base alla profondità dei dati disponibili
# su API-Sports: standings, statistiche avanzate, infortuni, quote reali.
#
# ALTA:  standings + stats avanzate + infortuni + quote reali quasi sempre disponibili
# MEDIA: dati buoni ma con qualche lacuna (es. infortuni parziali, quote non sempre reali)
# BASSA: fallback pesanti attivi (no standings, no infortuni, stats scarse)
LIVELLO_AFFIDABILITA = {
    # ── ALTA — Top 5 Europei + Coppe Europee ────────────────────────────────
    "🇪🇺 Champions League": "ALTA", "🇪🇺 Europa League": "ALTA", "🇪🇺 Conference League": "ALTA",
    "🇮🇹 Serie A": "ALTA", "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": "ALTA", "🇪🇸 La Liga": "ALTA",
    "🇩🇪 Bundesliga": "ALTA", "🇫🇷 Ligue 1": "ALTA",

    # ── MEDIA — Seconde linee Top 5 + campionati europei consolidati ───────
    "🇮🇹 Serie B": "MEDIA", "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Championship": "MEDIA",
    "🇳🇱 Eerste Divisie": "MEDIA", "🇩🇪 2. Bundesliga": "MEDIA", "🇪🇸 La Liga 2": "MEDIA",
    "🇳🇱 Eredivisie": "MEDIA", "🇵🇹 Primeira Liga": "MEDIA",
    "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Prem.": "MEDIA", "🇹🇷 Süper Lig": "MEDIA", "🇧🇪 Pro League": "MEDIA",
    "🇬🇷 Super League": "MEDIA", "🇨🇭 Super League": "MEDIA", "🇦🇹 Bundesliga": "MEDIA",
    "🇸🇦 Saudi Pro League": "MEDIA",
    "🇧🇷 Brasileirão Série A": "MEDIA", "🇦🇷 Liga Profesional": "MEDIA",
    "🇲🇽 Liga MX": "MEDIA", "🇺🇸 MLS": "MEDIA",
    "🇮🇹 Coppa Italia": "MEDIA", "🏴󠁧󠁢󠁥󠁮󠁧󠁿 FA Cup": "MEDIA", "🇪🇸 Copa del Rey": "MEDIA",
    "🇩🇪 DFB Pokal": "MEDIA", "🇫🇷 Coupe de France": "MEDIA",

    # ── BASSA — Leghe minori, playoff, coppe minori, sudamericani minori ───
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 League One": "BASSA", "🏴󠁧󠁢󠁥󠁮󠁧󠁿 League Two": "BASSA",
    "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Championship": "BASSA", "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish League One": "BASSA",
    "🇳🇴 Eliteserien": "BASSA", "🇳🇴 1. divisjon (Playoff NO)": "BASSA",
    "🇸🇪 Allsvenskan": "BASSA", "🇸🇪 Superettan (Playoff SE)": "BASSA",
    "🇫🇮 Veikkausliiga": "BASSA", "🇫🇮 Ykkönen (Playoff FI)": "BASSA",
    "🇩🇰 Superliga": "BASSA", "🇩🇰 1. Division (Playoff DK)": "BASSA",
    "🇧🇷 Brasileirão Série B": "BASSA", "🇨🇱 Primera División Chile": "BASSA",
    "🇺🇾 Primera División Uruguay": "BASSA", "🇨🇴 Liga BetPlay": "BASSA",
    "🇵🇪 Liga 1 Perù": "BASSA", "🇪🇨 LigaPro Ecuador": "BASSA",
    "🇧🇴 División Profesional": "BASSA", "🇵🇾 División Profesional PY": "BASSA",
    "🇻🇪 Liga FUTVE": "BASSA",
    "🇫🇮 Finnish Cup": "BASSA", "🇳🇴 Norwegian Cup": "BASSA",
    "🇸🇪 Svenska Cupen": "BASSA", "🇩🇰 DBU Pokalen": "BASSA",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 EFL Cup": "BASSA", "🇳🇱 KNVB Beker": "BASSA", "🇵🇹 Taça de Portugal": "BASSA",
    "🇧🇪 Croky Cup": "BASSA", "🇹🇷 Türkiye Kupası": "BASSA", "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Cup": "BASSA",
    "🇨🇭 Schweizer Cup": "BASSA", "🇦🇹 ÖFB Cup": "BASSA",
}

AFFIDABILITA_ORDINE = {"ALTA": 3, "MEDIA": 2, "BASSA": 1}
AFFIDABILITA_BADGE = {
    "ALTA":  ("🟢", "#22c55e", "Dati completi"),
    "MEDIA": ("🟡", "#f59e0b", "Dati parziali"),
    "BASSA": ("🔴", "#ef4444", "Dati limitati — stime da momentum"),
}

def get_affidabilita(nome_lega: str) -> str:
    return LIVELLO_AFFIDABILITA.get(nome_lega, "MEDIA")   # default prudente

# Campionati che usano anno solare come stagione
LEGHE_ANNO_SOLARE = {
    "🇳🇴 Eliteserien", "🇳🇴 1. divisjon (Playoff NO)",
    "🇸🇪 Allsvenskan", "🇸🇪 Superettan (Playoff SE)",
    "🇫🇮 Veikkausliiga", "🇫🇮 Ykkönen (Playoff FI)",
    "🇩🇰 Superliga", "🇩🇰 1. Division (Playoff DK)",
    "🇧🇷 Brasileirão Série A", "🇧🇷 Brasileirão Série B",
    "🇦🇷 Liga Profesional",
    "🇨🇱 Primera División Chile", "🇺🇾 Primera División Uruguay",
    "🇨🇴 Liga BetPlay", "🇵🇪 Liga 1 Perù", "🇪🇨 LigaPro Ecuador",
    "🇧🇴 División Profesional", "🇵🇾 División Profesional PY",
    "🇻🇪 Liga FUTVE", "🇲🇽 Liga MX", "🇺🇸 MLS",
}

# Campionati con playoff integrati (standings speciali o gironi multipli)
LEGHE_PLAYOFF = {
    "🇳🇴 1. divisjon (Playoff NO)", "🇸🇪 Superettan (Playoff SE)",
    "🇫🇮 Ykkönen (Playoff FI)", "🇩🇰 1. Division (Playoff DK)",
    "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Championship", "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish League One",
    "🇧🇷 Brasileirão Série B", "🇦🇷 Liga Profesional",
}

COPPE_EUROPEE = {"🇪🇺 Champions League", "🇪🇺 Europa League", "🇪🇺 Conference League"}
LEGHE_CIECHE  = {41, 42}   # League One/Two: radar infortuni offline

# ==========================================
# 🕵️ AUTO-DISCOVERY ID LEGA (Risolve Norvegia e altri)
# ==========================================
@st.cache_data(ttl=86400)
def trova_vero_id_lega(nazione: str, nome: str, fallback_id: int) -> int:
    """
    Interroga /leagues per trovare l'ID corretto di una lega per nome+nazione.
    Risolve il problema dell'Eliteserien norvegese che cambia ID o ritorna vuoto.
    """
    try:
        resp = requests.get(
            "https://v3.football.api-sports.io/leagues",
            headers=HEADERS,
            params={'country': nazione, 'name': nome},
            timeout=6
        ).json()
        if resp.get('response'):
            return resp['response'][0]['league']['id']
    except Exception:
        pass
    return fallback_id

@st.cache_data(ttl=86400)
def trova_id_multipli(nazione: str, fallback_map: dict) -> dict:
    """
    Per campionati nordici: recupera tutti i campionati di una nazione
    e restituisce un dict {nome_lega: id} per disambiguare.
    Risolve il problema Norvegia dove /leagues?country=Norway ritorna
    sia Eliteserien (calcio) che Eliteserien (futsal/handball).
    """
    try:
        resp = requests.get(
            "https://v3.football.api-sports.io/leagues",
            headers=HEADERS,
            params={'country': nazione, 'type': 'League'},
            timeout=6
        ).json()
        result = {}
        for entry in resp.get('response', []):
            nome = entry['league']['name']
            lid  = entry['league']['id']
            result[nome] = lid
        return result if result else fallback_map
    except Exception:
        return fallback_map

# Risoluzione runtime ID Norvegia (il problema principale)
_no_leagues = trova_id_multipli("Norway", {"Eliteserien": 69, "Norwegian First Division": 70})
MASTER_LEAGUES["🇳🇴 Eliteserien"]              = _no_leagues.get("Eliteserien", 69)
MASTER_LEAGUES["🇳🇴 1. divisjon (Playoff NO)"] = _no_leagues.get("Norwegian First Division", 70)

# ==========================================
# 🏆 AUTO-DISCOVERY COPPE NAZIONALI
# ==========================================
# Le coppe nazionali hanno ID che cambiano ogni stagione su API-Sports.
# Invece di hardcodarli, li troviamo automaticamente per nome+nazione.
# I fallback sono gli ID più comuni osservati storicamente.

@st.cache_data(ttl=86400)
def trova_id_coppa(nazione: str, nome_coppa: str, fallback_id: int) -> int:
    """Trova l'ID di una coppa nazionale cercando per nome e nazione."""
    try:
        resp = requests.get(
            "https://v3.football.api-sports.io/leagues",
            headers=HEADERS,
            params={'country': nazione, 'name': nome_coppa, 'type': 'Cup'},
            timeout=6
        ).json()
        if resp.get('response'):
            return resp['response'][0]['league']['id']
    except Exception:
        pass
    return fallback_id

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

# Aggiungi tutte le coppe ai set corretti
_coppe_nomi = {
    "🇫🇮 Finnish Cup", "🇳🇴 Norwegian Cup", "🇸🇪 Svenska Cupen", "🇩🇰 DBU Pokalen",
    "🇮🇹 Coppa Italia", "🏴󠁧󠁢󠁥󠁮󠁧󠁿 FA Cup", "🏴󠁧󠁢󠁥󠁮󠁧󠁿 EFL Cup", "🇪🇸 Copa del Rey",
    "🇩🇪 DFB Pokal", "🇫🇷 Coupe de France", "🇳🇱 KNVB Beker",
    "🇵🇹 Taça de Portugal", "🇧🇪 Croky Cup", "🇹🇷 Türkiye Kupası",
    "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Cup", "🇨🇭 Schweizer Cup", "🇦🇹 ÖFB Cup",
}
# Le coppe nordiche usano anno solare come stagione
LEGHE_ANNO_SOLARE.update({
    "🇫🇮 Finnish Cup", "🇳🇴 Norwegian Cup",
    "🇸🇪 Svenska Cupen", "🇩🇰 DBU Pokalen",
})
# Tutte le coppe sono trattate come coppe (peso momentum 80%, motivazione alta)
COPPE_NAZIONALI = _coppe_nomi

# ==========================================
# 📡 MODULI API — DATI GENERALI
# ==========================================
@st.cache_data(ttl=3600)
def get_active_leagues(start_date, end_date):
    active_ids = set()
    days = min((end_date - start_date).days + 1, 7)
    try:
        for i in range(days):
            d_str = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
            resp = requests.get(
                "https://v3.football.api-sports.io/fixtures",
                headers=HEADERS, params={'date': d_str}, timeout=8
            ).json()
            if 'response' in resp:
                active_ids.update({f['league']['id'] for f in resp['response']})
        return {k: v for k, v in MASTER_LEAGUES.items() if v in active_ids}
    except Exception:
        return MASTER_LEAGUES

@st.cache_data(ttl=86400)
def get_player_advanced_stats(player_id: int, season: str):
    """
    MIGLIORIA star player: usa rating + % da titolare + storico multi-stagione.
    Risolve il caso Dumfries: pochi minuti per infortunio ma è comunque star.
    """
    if not player_id:
        return "Unknown", 0, 0, 6.0, 0
    try:
        # Stagione corrente
        resp = requests.get(
            "https://v3.football.api-sports.io/players",
            headers=HEADERS, params={'id': player_id, 'season': season}, timeout=8
        ).json()
        # Stagione precedente (per capire se è titolare strutturale)
        season_prev = str(int(str(season)) - 1)
        resp_prev = requests.get(
            "https://v3.football.api-sports.io/players",
            headers=HEADERS, params={'id': player_id, 'season': season_prev}, timeout=8
        ).json()

        pos = "Unknown"
        tot_mins = tot_goals = tot_assists = 0
        mins_prev = 0
        ratings = []
        titolare_pct = 0.0

        for stat in resp.get('response', [{}])[0].get('statistics', []):
            if pos == "Unknown" and stat['games'].get('position'):
                pos = stat['games']['position']
            tot_mins    += stat['games'].get('minutes')  or 0
            tot_goals   += stat['goals'].get('total')    or 0
            tot_assists += stat['goals'].get('assists')  or 0
            if stat['games'].get('rating'):
                ratings.append(float(stat['games']['rating']))
            app   = stat['games'].get('appearences') or 0
            start = stat['games'].get('lineups')      or 0
            if app > 0:
                titolare_pct = max(titolare_pct, start / app)

        for stat in resp_prev.get('response', [{}])[0].get('statistics', []):
            mins_prev += stat['games'].get('minutes') or 0

        avg_rating = sum(ratings) / len(ratings) if ratings else 6.0

        # LOGICA STAR CORRETTA — almeno uno dei criteri:
        # 1. Qualità alta (rating indipendente dai minuti)
        # 2. Titolare abituale (>70% partite disponibili)
        # 3. Titolare strutturale in entrambe le stagioni
        # 4. Caso Dumfries: era titolare fisso l'anno scorso + buon rating ora
        is_star = (
            avg_rating >= 7.0
            or titolare_pct >= 0.70
            or (tot_mins >= 1200 and mins_prev >= 1800)
            or (mins_prev >= 2000 and avg_rating >= 6.7)
        )
        return pos, tot_goals, tot_assists, avg_rating, tot_mins
    except Exception:
        pass
    return "Unknown", 0, 0, 6.0, 0

def analizza_infortuni_pesati_v90(inf_list: list, season_lega: str):
    malus_att = boost_opp = 0.0
    t1_star = t2_rot = t3_ris = squalificati = difensori_out = 0
    portiere_titolare_out = False
    visti: set = set()
    for i in inf_list:
        p_id = i['player'].get('id')
        if not p_id or p_id in visti:
            continue
        visti.add(p_id)
        motivo = str(i.get('type', '')).lower()
        if 'suspend' in motivo or 'red card' in motivo or 'card' in motivo:
            squalificati += 1
        pos, gol, assist, rating, mins = get_player_advanced_stats(p_id, season_lega)
        is_star = mins >= 1200 or rating >= 7.0
        if is_star:           t1_star += 1
        elif mins >= 400:     t2_rot  += 1
        else:                 t3_ris  += 1
        if gol >= 5 or assist >= 5 or (pos in ["Attacker", "Midfielder"] and is_star):
            malus_att += 0.15
            if gol >= 10:     malus_att += 0.10
            if assist >= 8:   malus_att += 0.10
            if rating >= 7.3: malus_att += 0.10
        if pos == "Defender":
            if is_star:
                boost_opp += 0.15; difensori_out += 1
            elif mins >= 400:
                boost_opp += 0.05; difensori_out += 1
        elif pos == "Goalkeeper" and is_star:
            portiere_titolare_out = True; boost_opp += 0.25
    if difensori_out >= 2:
        boost_opp += 0.20
    return (min(0.60, malus_att), min(0.60, boost_opp),
            t1_star, t2_rot, t3_ris, len(visti), squalificati,
            portiere_titolare_out, difensori_out)

@st.cache_data(ttl=3600)
def scarica_quote_native(league_id: int, date_str: str, season_lega):
    try:
        resp = requests.get(
            "https://v3.football.api-sports.io/odds",
            headers=HEADERS,
            params={'league': league_id, 'season': season_lega, 'date': date_str, 'bookmaker': 8},
            timeout=8
        ).json()
        qd = {}
        for item in resp.get('response', []):
            fid = item['fixture']['id']
            qd[fid] = {}
            if item['bookmakers']:
                for bet in item['bookmakers'][0]['bets']:
                    if bet['id'] == 1:
                        for v in bet['values']:
                            if v['value'] == 'Home':      qd[fid]['1'] = float(v['odd'])
                            elif v['value'] == 'Draw':    qd[fid]['X'] = float(v['odd'])
                            elif v['value'] == 'Away':    qd[fid]['2'] = float(v['odd'])
                    elif bet['id'] == 5:
                        for v in bet['values']:
                            lbl = v['value']
                            if 'Over'  in lbl: qd[fid][f"O{lbl.split(' ')[1]}"] = float(v['odd'])
                            elif 'Under' in lbl: qd[fid][f"U{lbl.split(' ')[1]}"] = float(v['odd'])
                    elif bet['id'] == 12:
                        for v in bet['values']:
                            if v['value'] == 'Home/Draw':   qd[fid]['1X'] = float(v['odd'])
                            elif v['value'] == 'Draw/Away': qd[fid]['X2'] = float(v['odd'])
                            elif v['value'] == 'Home/Away': qd[fid]['12'] = float(v['odd'])
                    elif bet['id'] == 6:
                        for v in bet['values']:
                            if v['value'] == 'Yes':   qd[fid]['Goal']   = float(v['odd'])
                            elif v['value'] == 'No':  qd[fid]['NoGoal'] = float(v['odd'])
        return qd
    except Exception:
        return {}

@st.cache_data(ttl=86400)
def analizza_statistiche_stagionali(league_id: int, team_id: int, season_lega):
    try:
        resp = requests.get(
            "https://v3.football.api-sports.io/teams/statistics",
            headers=HEADERS,
            params={'league': league_id, 'season': season_lega, 'team': team_id},
            timeout=8
        ).json()
        stats = resp.get('response', {})
        if not stats:
            return 0.0, 0.0
        giocate = stats.get('fixtures', {}).get('played', {}).get('total', 0)
        if giocate == 0:
            return 0.0, 0.0
        cs_p  = (stats.get('clean_sheet', {}).get('total', 0) / giocate) * 100
        fts_p = (stats.get('failed_to_score', {}).get('total', 0) / giocate) * 100
        # Cap: su campioni piccoli (playoff, inizio stagione) i % possono essere 100/0 — irrealistici
        cs_p  = min(85.0, cs_p)
        fts_p = min(85.0, fts_p)
        return cs_p, fts_p
    except Exception:
        return 0.0, 0.0

@st.cache_data(ttl=1800)
def analizza_statistiche_avanzate_pro(team_id: int):
    """
    Cached 30min.
    MIGLIORIA 1: Cinismo corretto — sottrae i rigori dal calcolo.
    MIGLIORIA 2: Storico casa/trasferta separato per xG più preciso.
    """
    try:
        resp = requests.get(
            "https://v3.football.api-sports.io/fixtures",
            headers=HEADERS, params={"team": team_id, "last": 10, "status": "FT"}, timeout=8
        ).json()
        matches = resp.get("response", [])

        tot_poss = tot_tiri = tot_area = tot_gf = tot_gs = 0
        tot_corn = tot_cart = tot_falli = tot_par = tot_rigori = 0
        mv_stats = mv_goals = sq_certi = 0

        # MIGLIORIA 2: contatori separati casa/trasferta
        gf_home = gs_home = n_home = 0
        gf_away = gs_away = n_away = 0

        for i, m in enumerate(matches):
            fid     = m["fixture"]["id"]
            is_home = str(m["teams"]["home"]["id"]) == str(team_id)
            gf = m["goals"]["home"] if is_home else m["goals"]["away"]
            gs = m["goals"]["away"] if is_home else m["goals"]["home"]
            if gf is not None and gs is not None:
                tot_gf += int(gf); tot_gs += int(gs); mv_goals += 1
                # Split casa/trasferta
                if is_home:
                    gf_home += int(gf); gs_home += int(gs); n_home += 1
                else:
                    gf_away += int(gf); gs_away += int(gs); n_away += 1

            if i == 0:
                ev = requests.get(
                    "https://v3.football.api-sports.io/fixtures/events",
                    headers=HEADERS, params={"fixture": fid}, timeout=8
                ).json()
                for e in ev.get("response", []):
                    if str(e["team"]["id"]) == str(team_id):
                        if e["type"] == "Card" and "Red" in e.get("detail", ""):
                            sq_certi += 1

            sr = requests.get(
                "https://v3.football.api-sports.io/fixtures/statistics",
                headers=HEADERS, params={"fixture": fid}, timeout=8
            ).json()
            for ts in sr.get("response", []):
                if str(ts["team"]["id"]) == str(team_id):
                    s = {x["type"]: x["value"] for x in ts["statistics"]}
                    poss = str(s.get("Ball Possession", "50%")).replace("%", "")
                    tot_poss  += int(poss) if poss.isdigit() else 50
                    tot_tiri  += int(s.get("Shots on Goal", 0)    or 0)
                    tot_area  += int(s.get("Shots insidebox", 0)  or 0)
                    tot_corn  += int(s.get("Corner Kicks", 0)     or 0)
                    tot_falli += int(s.get("Fouls", 0)            or 0)
                    tot_par   += int(s.get("Goalkeeper Saves", 0) or 0)
                    tot_cart  += int(s.get("Yellow Cards", 0) or 0) + int(s.get("Red Cards", 0) or 0)
                    # MIGLIORIA 1: estrai rigori segnati
                    tot_rigori += int(s.get("Penalty Goals", 0) or 0)
                    mv_stats   += 1

        if mv_stats == 0: mv_stats = 1
        if mv_goals == 0: mv_goals = 1

        avg_poss  = tot_poss  / mv_stats
        avg_tiri  = tot_tiri  / mv_stats
        avg_area  = tot_area  / mv_stats
        avg_corn  = tot_corn  / mv_stats
        avg_cart  = tot_cart  / mv_stats
        avg_falli = tot_falli / mv_stats
        avg_par   = tot_par   / mv_stats
        avg_gf    = tot_gf    / mv_goals
        avg_gs    = tot_gs    / mv_goals
        avg_rig   = tot_rigori / mv_goals

        # MIGLIORIA 1: Cinismo da gioco (esclude rigori)
        gol_da_gioco  = max(0.1, avg_gf  - avg_rig)
        tiri_da_gioco = max(0.1, avg_tiri - avg_rig)
        conv = tiri_da_gioco / gol_da_gioco if gol_da_gioco > 0 else 10.0
        conv = max(2.0, conv)   # floor: fisicamente impossibile segnare con meno di 2 tiri/gol in media

        # MIGLIORIA 2: medie casa/trasferta (usate per xG splitting)
        avg_gf_home = gf_home / max(1, n_home)
        avg_gs_home = gs_home / max(1, n_home)
        avg_gf_away = gf_away / max(1, n_away)
        avg_gs_away = gs_away / max(1, n_away)

        if avg_poss > 55 and avg_area < 4:   stile = "Tiki-Taka Sterile"
        elif avg_poss < 45 and avg_area > 4: stile = "Verticale Diretto"
        else:                                 stile = "Bilanciato"

        # Return esteso: aggiunge avg_rig, avg_gf_home, avg_gs_home, avg_gf_away, avg_gs_away
        return (avg_poss, avg_tiri, avg_area, conv, avg_corn, avg_cart, avg_falli, avg_par,
                stile, sq_certi, avg_gf, avg_gs,
                avg_rig, avg_gf_home, avg_gs_home, avg_gf_away, avg_gs_away)
    except Exception:
        return (50.0, 4.0, 5.0, 5.0, 4.5, 2.0, 10.0, 2.5,
                "Bilanciato", 0, 1.0, 1.0, 0.0, 1.0, 1.0, 1.0, 1.0)


# ==========================================
# 📊 CORE — CALCOLO MERCATI (POISSON)
# ==========================================
def calcola_prob_poisson(xg: float, gol: int) -> float:
    return ((xg ** gol) * math.exp(-xg)) / math.factorial(gol)

def calcola_tutti_i_mercati(xg_c: float, xg_t: float,
                             avg_corner: float, avg_cart: float,
                             is_sev: bool, tot_falli: float) -> dict:
    """
    FIX: Combo con probabilità congiunta corretta.
    FIX: HT/FT normalizzato (ht_prob in decimali, p[ft] diviso 100).
    """
    p = {"1": 0, "X": 0, "2": 0, "1X": 0, "X2": 0, "12": 0,
         "Goal": 0, "NoGoal": 0, "Pari": 0, "Dispari": 0,
         "Casa O0.5": 0, "Ospite O0.5": 0}
    mg = {"MG 1-3": 0, "MG 1-4": 0, "MG 2-3": 0, "MG 2-4": 0, "MG 2-5": 0, "MG 3-4": 0}
    for line in [1.5, 2.5, 3.5, 4.5]:
        p[f"U{line}"] = 0; p[f"O{line}"] = 0
    re_prob = {}

    for gc in range(8):
        for gt in range(8):
            prob = calcola_prob_poisson(xg_c, gc) * calcola_prob_poisson(xg_t, gt) * 100.0
            tot  = gc + gt
            if gc > gt:   p["1"] += prob
            elif gc == gt: p["X"] += prob
            else:          p["2"] += prob
            if gc > 0 and gt > 0: p["Goal"]   += prob
            else:                  p["NoGoal"] += prob
            if tot % 2 == 0: p["Pari"]    += prob
            else:             p["Dispari"] += prob
            for line in [1.5, 2.5, 3.5, 4.5]:
                if tot < line: p[f"U{line}"] += prob
                else:          p[f"O{line}"] += prob
            if gc > 0: p["Casa O0.5"]   += prob
            if gt > 0: p["Ospite O0.5"] += prob
            if 1 <= tot <= 3: mg["MG 1-3"] += prob
            if 1 <= tot <= 4: mg["MG 1-4"] += prob
            if 2 <= tot <= 3: mg["MG 2-3"] += prob
            if 2 <= tot <= 4: mg["MG 2-4"] += prob
            if 2 <= tot <= 5: mg["MG 2-5"] += prob
            if 3 <= tot <= 4: mg["MG 3-4"] += prob
            if gc <= 4 and gt <= 4:
                re_prob[f"Risultato {gc}-{gt}"] = prob

    p["1X"] = p["1"] + p["X"]
    p["X2"] = p["X"] + p["2"]
    p["12"] = p["1"] + p["2"]

    if xg_c > 1.2 and xg_t > 1.2:
        p["Goal"]   = min(90.0, p["Goal"] * 1.18)
        p["NoGoal"] = max(10.0, 100.0 - p["Goal"])
    elif xg_c < 0.9 and xg_t < 0.9:
        p["NoGoal"] = min(90.0, p["NoGoal"] * 1.15)
        p["Goal"]   = max(10.0, 100.0 - p["NoGoal"])

    # FIX: probabilità congiunta corretta per combo
    combos = {
        "1X + Over 1.5":   (p["1X"]   / 100) * (p["O1.5"] / 100) * 100 * 0.92,
        "X2 + Over 1.5":   (p["X2"]   / 100) * (p["O1.5"] / 100) * 100 * 0.92,
        "1X + Under 3.5":  (p["1X"]   / 100) * (p["U3.5"] / 100) * 100 * 0.95,
        "X2 + Under 3.5":  (p["X2"]   / 100) * (p["U3.5"] / 100) * 100 * 0.95,
        "1 + Over 2.5":    (p["1"]    / 100) * (p["O2.5"] / 100) * 100 * 0.90,
        "2 + Over 2.5":    (p["2"]    / 100) * (p["O2.5"] / 100) * 100 * 0.90,
        "Goal + Over 2.5": (p["Goal"] / 100) * (p["O2.5"] / 100) * 100 * 0.95,
    }

    # FIX: HT/FT normalizzato correttamente
    ht_raw  = {"1": p["1"] * 0.9, "X": p["X"] * 1.5, "2": p["2"] * 0.9}
    tot_ht  = sum(ht_raw.values())
    ht_prob = {k: v / tot_ht for k, v in ht_raw.items()}   # decimali (somma=1)
    htft    = {f"HT/FT {ht}/{ft}": ht_prob[ht] * (p[ft] / 100.0) * 100.0
               for ht in ["1", "X", "2"] for ft in ["1", "X", "2"]}

    prob_corner = min(92.0, max(15.0, (avg_corner / 9.5) * 55))
    tension     = avg_cart + (1.5 if is_sev else 0) + (tot_falli / 20.0)
    prob_cart   = min(88.0, max(20.0, (tension / 5.0) * 55))

    special = {"Over 8.5 Angoli": prob_corner, "Over 4.5 Cartellini": prob_cart}
    return {**p, **mg, **re_prob, **combos, **htft, **special}

# ==========================================
# 💰 QUOTA, VALUE BET, KELLY
# ==========================================
def get_quota_finale(tip: str, prob: float, quote_reali: dict):
    """FIX: margine realistico 7% invece di 1.55x arbitrario."""
    if quote_reali and tip in quote_reali:
        return quote_reali[tip], True
    if prob <= 0:
        return 99.0, False
    return max(1.01, round((100.0 / prob) * MARGINE_BK, 2)), False

def calcola_edge_pct(prob: float, quota: float) -> float:
    return ((prob / 100.0) * quota - 1.0) * 100.0

def kelly_fraction(prob: float, quota: float, fraz: float = 0.25) -> float:
    p = prob / 100.0; b = quota - 1.0
    if b <= 0: return 0.0
    return max(0.0, ((b * p - (1 - p)) / b) * fraz)

# ==========================================
# 🔎 ANALISI SQUADRA & H2H

# Frequenze medie attese per mercato (base statistica europea)
FREQUENZE_MEDIE = {
    'W': 3.0, 'X': 3.5, 'L': 3.0, 'Over': 2.0, 'Goal': 2.2
}

@st.cache_data(ttl=3600)
def analizza_squadra_globale(team_id: int):
    """
    MIGLIORIA ritardi: conta partite consecutive senza evento
    e confronta con la frequenza media attesa.
    Ritorna anche punti_5 e punti_prev_5 per il calcolo pressione.
    """
    try:
        resp = requests.get(
            "https://v3.football.api-sports.io/fixtures",
            headers=HEADERS, params={'team': team_id, 'last': 10, 'status': 'FT'}, timeout=8
        ).json()
        matches = resp.get('response', [])
        if not matches:
            return 1.0, False, "N/D", 1.0, [], 0, 0

        ultima_data  = datetime.strptime(matches[0]['fixture']['date'][:10], '%Y-%m-%d')
        diff_giorni  = (datetime.now() - ultima_data).days
        is_stanca    = diff_giorni <= 4
        m_stanchezza = 0.95 if is_stanca else 1.0

        # Forma ultime 5 + punti split per pressione
        forma_str = ""; punti_5 = 0; punti_prev_5 = 0
        for i, m in enumerate(matches[:10]):
            is_home = str(m['teams']['home']['id']) == str(team_id)
            gh, ga  = m['goals']['home'], m['goals']['away']
            if gh is None: continue
            if gh == ga:   pt = 1; ch = "D"
            elif (is_home and gh > ga) or (not is_home and ga > gh): pt = 3; ch = "W"
            else:          pt = 0; ch = "L"
            if i < 5:
                forma_str += ch; punti_5 += pt
            else:
                punti_prev_5 += pt
        forma_str = forma_str[::-1]
        m_forma   = 0.9 + (punti_5 / 15) * 0.2

        # Ritardi pesati — contatore consecutivo
        consec = {'W': 0, 'X': 0, 'L': 0, 'Over': 0, 'Goal': 0}
        for m in matches:
            is_home = str(m['teams']['home']['id']) == str(team_id)
            gh, ga  = m['goals']['home'], m['goals']['away']
            if gh is None or ga is None: continue
            # W/D/L
            if gh == ga:
                consec['X'] = 0; consec['W'] += 1; consec['L'] += 1
            elif (is_home and gh > ga) or (not is_home and ga > gh):
                consec['W'] = 0; consec['X'] += 1; consec['L'] += 1
            else:
                consec['L'] = 0; consec['W'] += 1; consec['X'] += 1
            # Over/Goal
            if (gh + ga) > 2: consec['Over'] = 0
            else:              consec['Over'] += 1
            if gh > 0 and ga > 0: consec['Goal'] = 0
            else:                  consec['Goal'] += 1

        # Costruisci lista ritardi con peso
        ritardi = []
        for evento, n in consec.items():
            media = FREQUENZE_MEDIE[evento]
            if n >= media:
                peso = n / media
                if peso >= 2.5:   livello = "🔴"
                elif peso >= 1.5: livello = "🟠"
                else:             livello = "🟡"
                label_map = {'W':'Vittoria','X':'Pareggio','L':'Sconfitta',
                             'Over':'Over 2.5','Goal':'Goal'}
                ritardi.append({
                    'evento': evento,
                    'partite': n,
                    'peso': peso,
                    'livello': livello,
                    'label': f"{livello} {label_map[evento]}: {n}p ({peso:.1f}x media)"
                })

        return m_stanchezza, is_stanca, forma_str, m_forma, ritardi, punti_5, punti_prev_5
    except Exception:
        return 1.0, False, "N/D", 1.0, [], 0, 0

@st.cache_data(ttl=3600)
def analizza_h2h_dna_e_andata(id_casa: int, id_trasf: int):
    try:
        resp = requests.get(
            "https://v3.football.api-sports.io/fixtures/headtohead",
            headers=HEADERS, params={'h2h': f"{id_casa}-{id_trasf}", 'last': 5}, timeout=8
        ).json()
        matches = resp.get('response', [])
        if not matches:
            return 1.0, 1.0, 0, 0, "Nessun Precedente", 1.0, 1.0, "", "Nessun match."
        vittorie_c = vittorie_t = gol_c = gol_t = 0
        andata_msg = ""; boost_c = boost_t = 1.0
        dettagli = []
        for m in matches:
            if m['goals']['home'] is not None:
                d_m = datetime.strptime(m['fixture']['date'][:10], '%Y-%m-%d').strftime('%d/%m/%Y')
                dettagli.append(f"📅 {d_m}: {m['teams']['home']['name']} "
                                 f"<b>{m['goals']['home']} - {m['goals']['away']}</b> "
                                 f"{m['teams']['away']['name']}")
        det_str = "<br>".join(dettagli) if dettagli else "Nessun dato."
        ult = matches[0]
        data_ult = datetime.strptime(ult['fixture']['date'][:10], '%Y-%m-%d')
        if (datetime.now() - data_ult).days <= 28:
            ih = ult['teams']['home']['id'] == id_casa
            gc_l = ult['goals']['home']; gt_l = ult['goals']['away']
            if gc_l is not None and gt_l is not None:
                g_c = gc_l if ih else gt_l; g_t = gt_l if ih else gc_l
                diff = g_c - g_t
                andata_msg = f"🏆 Andata: {g_c} - {g_t}"
                if diff in [-1, -2]:      boost_c = 1.25; andata_msg += " (Casa all'assalto ⚔️)"
                elif diff in [1, 2]:      boost_t = 1.25; andata_msg += " (Ospiti all'assalto ⚔️)"
                elif abs(diff) >= 3:      boost_c = boost_t = 0.85; andata_msg += " (Qualificazione chiusa 🛡️)"
        for m in matches:
            if m['goals']['home'] is None: continue
            ih = m['teams']['home']['id'] == id_casa
            gc = m['goals']['home'] if ih else m['goals']['away']
            gt = m['goals']['away'] if ih else m['goals']['home']
            gol_c += gc; gol_t += gt
            if gc > gt: vittorie_c += 1
            elif gt > gc: vittorie_t += 1
        cnt = max(1, len([m for m in matches if m['goals']['home'] is not None]))
        tot = max(1, gol_c + gol_t)
        m_h2h_c = min(1.20, max(0.80, 0.90 + (vittorie_c/cnt)*0.20 + (gol_c/(cnt*tot))*0.10))
        m_h2h_t = min(1.20, max(0.80, 0.90 + (vittorie_t/cnt)*0.20 + (gol_t/(cnt*tot))*0.10))
        storico = f"Vittorie: 🏠 {vittorie_c} - {vittorie_t} ✈️ | Gol H2H: {gol_c} a {gol_t}"
        return m_h2h_c, m_h2h_t, gol_c, gol_t, storico, boost_c, boost_t, andata_msg, det_str
    except Exception:
        return 1.0, 1.0, 0, 0, "Dati N/D", 1.0, 1.0, "", "Nessun dato."

@st.cache_data(ttl=3600)
def rileva_contesto_spareggio(fix_id: int, c_id: int, t_id: int,
                               league_id_c: int, league_id_t: int,
                               match_date_str: str) -> dict:
    """
    Rileva se la partita è:
    1. Uno spareggio inter-lega (squadre da serie diverse)
    2. Una gara di ritorno (c'è stata un'andata recente tra le stesse squadre)
    Ritorna un dict con i boost motivazionali corretti.
    """
    result = {
        'is_interlega': league_id_c != league_id_t,
        'is_ritorno': False,
        'aggregato_c': 0, 'aggregato_t': 0,
        'boost_c': 1.0, 'boost_t': 1.0,
        'msg': '', 'peso_momentum': 0.80
    }

    # Cerca andata recente (ultimi 60 giorni tra le stesse squadre)
    try:
        h2h = requests.get(
            "https://v3.football.api-sports.io/fixtures/headtohead",
            headers=HEADERS,
            params={'h2h': f"{c_id}-{t_id}", 'last': 4},
            timeout=8
        ).json()
        matches = h2h.get('response', [])
        for m in matches:
            if str(m['fixture']['id']) == str(fix_id):
                continue
            data_m = datetime.strptime(m['fixture']['date'][:10], '%Y-%m-%d')
            data_oggi = datetime.strptime(match_date_str, '%Y-%m-%d')
            giorni_fa = (data_oggi - data_m).days
            if 3 <= giorni_fa <= 21:   # finestra tipica andata/ritorno
                result['is_ritorno'] = True
                ih = m['teams']['home']['id'] == c_id
                gc = m['goals']['home'] if ih else m['goals']['away']
                gt = m['goals']['away'] if ih else m['goals']['home']
                if gc is not None and gt is not None:
                    result['aggregato_c'] = int(gc)
                    result['aggregato_t'] = int(gt)
                    diff = gc - gt
                    if diff > 0:
                        # Casa avanti nel ritorno: ospiti devono attaccare
                        result['boost_t'] = 1.30
                        result['boost_c'] = 0.90
                        result['msg'] = f"🔄 RITORNO | Aggregato: {gc}-{gt} (Ospiti all'assalto)"
                    elif diff < 0:
                        result['boost_c'] = 1.30
                        result['boost_t'] = 0.90
                        result['msg'] = f"🔄 RITORNO | Aggregato: {gc}-{gt} (Casa all'assalto)"
                    elif diff == 0:
                        result['boost_c'] = 1.20
                        result['boost_t'] = 1.20
                        result['msg'] = f"🔄 RITORNO | Aggregato: {gc}-{gt} (Tutto aperto ⚖️)"
                break
    except Exception:
        pass

    if result['is_interlega']:
        result['msg'] = (result['msg'] + " ⚡ SPAREGGIO INTER-LEGA").strip()
        result['peso_momentum'] = 1.0   # 100% momentum, standings non confrontabili

    return result

@st.cache_data(ttl=3600)
def scarica_meteo(citta: str):
    try:
        resp = requests.get(f"https://wttr.in/{citta}?format=j1", timeout=3).json()
        cond    = resp['current_condition'][0]['weatherDesc'][0]['value']
        pioggia = any(p in cond.lower() for p in ['rain', 'snow', 'shower', 'thunder'])
        return (0.90, f"🌧️ {cond}") if pioggia else (1.0, f"☀️ {cond}")
    except Exception:
        return 1.0, "🌥️ Dato N/D"

# ==========================================
# 🏗️ UTILITY
# ==========================================
def semplifica_nome(nome: str) -> str:
    """FIX: sostituzione conservativa — evita di troncare nomi come FCB."""
    for token in [' FC', ' AC', ' BC', ' AS', ' Calcio', ' AFC', ' SL']:
        nome = nome.replace(token, '')
    for token in ['FC ', 'AC ', 'AS ', 'AFC ', 'SL ']:
        if nome.startswith(token):
            nome = nome[len(token):]
    return nome.strip()

def get_family(tip: str) -> str:
    if tip in ["1", "X", "2", "1X", "X2", "12"]:                      return "1X2"
    if ("U" in tip or "O" in tip) and "+" not in tip \
        and "Casa" not in tip and "Ospite" not in tip \
        and "Angoli" not in tip and "Cartellini" not in tip:            return "UO"
    if "MG" in tip:                                                      return "MG"
    if "Goal" in tip or "NoGoal" in tip:                                return "GGNG"
    if "+" in tip:                                                       return "COMBO"
    if "Risultato" in tip:                                               return "RE"
    if "HT/FT" in tip:                                                   return "HTFT"
    if tip in ["Pari", "Dispari"]:                                       return "PD"
    if "Angoli" in tip or "Cartellini" in tip:                          return "SPECIAL"
    return "ALTRO"

def costruisci_schedina_dinamica(pool: list, min_q: float, max_q: float,
                                  target_mult: float, escludi_match=None,
                                  max_match_q: float = 5.0, max_righe: int = 12,
                                  max_same_family: int = 2):
    if escludi_match is None: escludi_match = set()
    valid = [x for x in pool
             if min_q <= float(x['Quota']) <= max_q
             and float(x['Quota']) <= max_match_q
             and float(x.get('Edge', 0)) > 0]   # solo scommesse con edge positivo reale
    pool_ord = sorted(valid, key=lambda x: calcola_edge_pct(x['Prob'], float(x['Quota'])), reverse=True)
    sel = []; viste = set(); fam_cnt = {}; q_tot = prob_tot = 1.0
    for item in pool_ord:
        fam  = get_family(item['Tip'])
        nome = item['Match']
        if (nome not in viste and nome not in escludi_match
                and fam_cnt.get(fam, 0) < max_same_family):
            sel.append(item); viste.add(nome)
            fam_cnt[fam] = fam_cnt.get(fam, 0) + 1
            q_tot    *= float(item['Quota'])
            prob_tot *= item['Prob'] / 100.0
        if q_tot >= target_mult or len(sel) >= max_righe: break
    return sel, q_tot, prob_tot, viste.union(escludi_match)

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

st.sidebar.markdown("**📅 Periodo di analisi**")
date_range = st.sidebar.date_input("", [])
if len(date_range) == 2:   start_date, end_date = date_range[0], date_range[1]
elif len(date_range) == 1: start_date = end_date = date_range[0]
else:                       start_date = end_date = datetime.now().date()
start_str = start_date.strftime('%Y-%m-%d')
end_str   = end_date.strftime('%Y-%m-%d')

st.sidebar.markdown("---")
budget_totale = st.sidebar.number_input("💰 Budget (€):", min_value=5.0, value=50.0, step=5.0)
st.sidebar.markdown("---")

if st.sidebar.button("🗑️ SVUOTA MEMORIA V90 (Hard Reset)"):
    st.cache_data.clear()
    st.session_state.data_master     = {}
    st.session_state.all_tips_global = []
    st.sidebar.success("✅ Cache svuotata!")

with st.sidebar:
    if st.button("🔍 Trova Campionati Attivi nel Periodo"):
        with st.spinner("Scansione palinsesto..."):
            st.session_state['active_leagues'] = get_active_leagues(start_date, end_date)

if 'active_leagues' not in st.session_state:
    st.session_state['active_leagues'] = MASTER_LEAGUES
active_dict = st.session_state['active_leagues']
if not active_dict: st.sidebar.warning("Nessun campionato supportato attivo.")

st.sidebar.markdown("---")
st.sidebar.markdown("**🎯 Filtro Affidabilità Dati**")
filtro_affidabilita = st.sidebar.multiselect(
    "Includi solo:",
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
    st.sidebar.warning("Nessun campionato nel livello di affidabilità selezionato.")

# Ordina i campionati per affidabilità (Alta prima) poi alfabetico
leghe_ordinate = sorted(
    leghe_filtrate.keys(),
    key=lambda n: (-AFFIDABILITA_ORDINE.get(get_affidabilita(n), 2), n)
)

scelte     = st.sidebar.multiselect("Campionati:", leghe_ordinate, default=leghe_ordinate)
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

    for name in scelte:
        f_id         = active_dict[name]
        is_coppa_eu  = name in COPPE_EUROPEE
        is_coppa_naz = name in COPPE_NAZIONALI
        is_coppa     = is_coppa_eu or is_coppa_naz
        is_anno_sol  = name in LEGHE_ANNO_SOLARE
        is_playoff   = name in LEGHE_PLAYOFF
        is_lega_cieca = f_id in LEGHE_CIECHE
        stagione_lega = start_date.year if is_anno_sol else STAGIONE

        with st.spinner(f"Analisi V90 {name}..."):
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

                m_st_c, is_stanca_c, forma_c, m_f_c, rit_c, punti_5_c, punti_prev_5_c = analizza_squadra_globale(db_stats[c_s]['id'])
                m_st_t, is_stanca_t, forma_t, m_f_t, rit_t, punti_5_t, punti_prev_5_t = analizza_squadra_globale(db_stats[t_s]['id'])
                cs_c, fts_c = analizza_statistiche_stagionali(f_id, db_stats[c_s]['id'], stagione_lega)
                cs_t, fts_t = analizza_statistiche_stagionali(f_id, db_stats[t_s]['id'], stagione_lega)
                m_met, d_met = scarica_meteo(c_s)
                (m_h2h_c, m_h2h_t, gol_h2h_c, gol_h2h_t, str_h2h,
                 b_and_c, b_and_t, andata_msg, det_h2h) = analizza_h2h_dna_e_andata(
                    db_stats[c_s]['id'], db_stats[t_s]['id'])

                # Rilevamento spareggio inter-lega e gara di ritorno
                ctx_spar = rileva_contesto_spareggio(
                    fix_id, db_stats[c_s]['id'], db_stats[t_s]['id'],
                    f_id, f_id, match_date_str)
                if ctx_spar['is_ritorno'] or ctx_spar['is_interlega']:
                    b_and_c *= ctx_spar['boost_c']
                    b_and_t *= ctx_spar['boost_t']
                    if ctx_spar['msg']:
                        andata_msg = ctx_spar['msg']
                is_interlega = ctx_spar['is_interlega']
                peso_mom_override = ctx_spar['peso_momentum'] if ctx_spar['is_interlega'] else None
                (poss_c, tiri_c, box_c, conv_c, corn_c, cart_c, falli_c,
                 par_c, stile_c, sq_cert_c, gf_10_c, gs_10_c,
                 rig_c, gf_home_c, gs_home_c, gf_away_c, gs_away_c) = analizza_statistiche_avanzate_pro(db_stats[c_s]['id'])
                (poss_t, tiri_t, box_t, conv_t, corn_t, cart_t, falli_t,
                 par_t, stile_t, sq_cert_t, gf_10_t, gs_10_t,
                 rig_t, gf_home_t, gs_home_t, gf_away_t, gs_away_t) = analizza_statistiche_avanzate_pro(db_stats[t_s]['id'])

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
                    gap_c = db_stats[c_s]['punti'] - db_stats[t_s]['punti']
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
                    punti_c  = db_stats[c_s]['punti']; punti_t  = db_stats[t_s]['punti']
                    rank_c   = db_stats[c_s]['rank'];  rank_t   = db_stats[t_s]['rank']
                    gioc_c   = db_stats[c_s]['giocate']; gioc_t = db_stats[t_s]['giocate']
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
                xg_st_c = math.sqrt(max(0.01, db_stats[c_s]['ac']) * max(0.01, db_stats[t_s]['dt']))
                xg_st_t = math.sqrt(max(0.01, db_stats[t_s]['at']) * max(0.01, db_stats[c_s]['dc']))
                # MIGLIORIA 2: xG momentum usa casa/trasferta separati
                # Casa gioca in casa → usiamo i suoi gol_fatti_in_casa vs gol_subiti_in_casa dell'avversario
                xg_mo_c = math.sqrt(max(0.01, gf_home_c) * max(0.01, gs_home_t))
                xg_mo_t = math.sqrt(max(0.01, gf_away_t) * max(0.01, gs_away_c))
                # Peso momentum: inter-lega=100%, coppe/playoff=80%, normale=30%
                if peso_mom_override is not None:
                    peso_mom = peso_mom_override
                elif is_coppa or is_playoff or db_stats[c_s]['giocate'] <= 5:
                    peso_mom = 0.80
                else:
                    peso_mom = 0.30
                peso_std  = 1.0 - peso_mom
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

                sg_c = "C.Sgombra" in msg_mot; sg_t = "O.Sgombra" in msg_mot
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

                best_key = max(["1","X","2"], key=lambda k: full_tips[k])
                if full_tips[best_key] < 45.0:
                    best_key = "No Segno Fisso"; best_prob = 0.0; best_q = "-"; best_real = False
                else:
                    best_prob = full_tips[best_key]
                    best_q, best_real = get_quota_finale(best_key, best_prob, quote_reali_match)

                for k, v in full_tips.items():
                    q_fin, is_real = get_quota_finale(k, v, quote_reali_match)
                    st.session_state.all_tips_global.append({
                        "Match":  f"{c_u} vs {t_u}", "League": name, "Tip": k,
                        "Prob":   v, "Quota": q_fin, "Real": is_real, "Time": orario_ita,
                        "Edge":   calcola_edge_pct(v, q_fin),
                        "Kelly":  kelly_fraction(v, q_fin),
                    })
                matches_list.append({
                    "orario": orario_ita, "c_u": c_u, "t_u": t_u, "c_s": c_s, "t_s": t_s,
                    "rank_c": db_stats[c_s]['rank'], "rank_t": db_stats[t_s]['rank'],
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
                })

            if matches_list:
                st.session_state.data_master[name] = matches_list

# ==========================================
# 🖥️ DISPLAY: 3 TAB
# ==========================================
# ── MAIN HEADER ──────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding: 28px 0 20px;">
  <div style="font-family:'Syne',sans-serif;font-size:2.4rem;font-weight:800;
    background:linear-gradient(135deg,#4f8ef7,#7c5cfc);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
    line-height:1;margin-bottom:6px;">
    🎯 MATRIX BET V90
  </div>
  <div style="font-size:0.85rem;color:#8b95b0;letter-spacing:0.05em;">
    Predictive Football Analytics — Powered by API-Sports & Poisson Model
  </div>
</div>
""", unsafe_allow_html=True)

if st.session_state.data_master:
    t1, t2, t3 = st.tabs(["🛒 TOP 10 & BUILDER", "🔬 ESPLORATORE PARTITE", "🏆 SCHEDINE AUTOMATICHE"])

    # ─── TAB 1 ──────────────────────────────────────────────────────────────────
    with t1:
        st.header("🛒 BET BUILDER & CLASSIFICHE OMNI-MARKET")
        st.info("💡 **Edge%** = valore della scommessa — mostrate solo scommesse con Edge positivo. "
                "**Kelly%** = puntata suggerita sul budget totale. "
                "⚠️ Su quote basse (< 1.50) il Kelly può essere 0% per via del margine sottile: "
                "in quel caso usa il 1-2% del budget come puntata minima.")

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
            cols = ['Match','Tip','Prob','Quota','Edge','Kelly','Time','League']
            df = df[cols].copy()   # .copy() evita che la modifica di Kelly corrompa all_tips_global
            df['Kelly'] = (df['Kelly'] * 100).round(1)
            # Colonna Affidabilità: badge visivo per capire quanto fidarsi del dato
            df['Aff'] = df['League'].apply(lambda l: AFFIDABILITA_BADGE[get_affidabilita(l)][0])
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
                hide_index=True, use_container_width=True,
                disabled=['Match','Tip','Prob','Quota','Edge','Kelly','Time','League','Aff'],
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
        sel_6  = mostra_tabella("🧨 Top 10 Azzardi (Quote ≥ 2.50)",
                                lambda t: True,
                                min_q=2.50, sort_by="Edge", solo_kelly_positivo=False)

        tutte = sel_1 + sel_2 + sel_3 + sel_4 + sel_mg + sel_co + sel_6
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
        else:
            st.info("👆 Spunta qualche voce dalle classifiche per costruire la schedina.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ─── TAB 2 ──────────────────────────────────────────────────────────────────
    with t2:
        st.write(f"Partite per il periodo **{start_str} / {end_str}**.")
        for camp, matches in st.session_state.data_master.items():
            aff = get_affidabilita(camp)
            aff_icon, aff_color, aff_desc = AFFIDABILITA_BADGE[aff]
            with st.expander(f"🏆 {camp}  {aff_icon}", expanded=False):
                st.markdown(
                    f"<span class='tag' style='background:{aff_color}22;border:1px solid {aff_color}55;"
                    f"color:{aff_color} !important;'>{aff_icon} Affidabilità {aff} — {aff_desc}</span>",
                    unsafe_allow_html=True)
                for m in sorted(matches, key=lambda x: x['orario']):
                    titolo_e = (f"🕒 {m['orario']} | 🏟️ {m['c_u']} vs {m['t_u']} | "
                                f"👑 {m['best_1x2'][0]}"
                                if m['best_1x2'][0] != "No Segno Fisso"
                                else f"🕒 {m['orario']} | 🏟️ {m['c_u']} vs {m['t_u']} | ⚠️ No Bet")
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
                            st.markdown(
                                f"<div class='top3-card'>"
                                f"<div class='section-header' style='margin-bottom:12px;'>"
                                f"<span style='font-family:Syne,sans-serif;font-weight:700;font-size:0.9rem;'>🔝 TOP 3 OMNI-MARKET</span></div>"
                                f"{rows}</div>", unsafe_allow_html=True)

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
        st.info("Budget allocato con **Kelly Criterion** (25% frazionato) — "
                "ogni fascia riceve un budget proporzionale al proprio edge medio reale.")

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
                (pool_s := [x for x in kp if x['Tip'] not in ["Goal","O1.5","O2.5","O3.5","O4.5"]],
                 1.12, 1.50, 2.0,  2.0,  set(),  bud_s),
                (kp,   1.51, 2.20, 5.0,  2.20, None,  bud_p),
                (kp,   2.21, 4.50, 30.0, 4.50, None,  bud_a),
            ]

            escludi_prev = set()
            for idx, (nome, emoji, cls, bg_col, acc_col, nota) in enumerate(SCHEDINE_CFG):
                pool_f, min_q, max_q, target, mq, _, budget = SCHEDINE_PARAMS[idx]
                escludi = escludi_prev

                slip, q_tot, prob, usate = costruisci_schedina_dinamica(
                    pool_f, min_q, max_q, target, escludi_match=escludi, max_match_q=mq)
                escludi_prev = usate
                vincita_tot = budget * q_tot

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
