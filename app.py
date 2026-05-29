import streamlit as st
import requests
import math
import pandas as pd
from datetime import datetime, timezone, timedelta
import pytz

# ==========================================
# 🎨 UI: MATRIX DESIGN V90 FIXED
# ==========================================
st.set_page_config(page_title="Matrix Bet V90", page_icon="🎯", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1a1a1a; }
    .stExpander { border: 1px solid #e1e4e8 !important; background-color: #ffffff !important;
        border-radius: 10px !important; box-shadow: 0 1px 4px rgba(0,0,0,0.03) !important;
        margin-bottom: 10px !important; }
    .stMetric { background-color: #fcfcfc; border: 1px solid #eee; padding: 12px; border-radius: 10px; }
    h1, h2, h3, p, span, label { color: #1a1a1a !important; font-family: 'Segoe UI', sans-serif; }
    .label-bold { font-weight: 700; color: #444; font-size: 0.85em;
        text-transform: uppercase; margin-bottom: 5px; display: block; }
    .strategy-box { padding: 20px; border-radius: 15px; margin-bottom: 20px;
        border: 2px solid #e1e4e8; }
    .safety-bg   { background-color: #f0fff4; border-color: #38a169; border-left: 5px solid #27ae60; }
    .performance-bg { background-color: #fffaf0; border-color: #dd6b20; border-left: 5px solid #d35400; }
    .risk-bg     { background-color: #fff5f5; border-color: #e53e3e; border-left: 5px solid #c0392b; }
    .builder-bg  { background-color: #f5f0ff; border-color: #805ad5; border-left: 5px solid #8e44ad; }
    .form-box    { letter-spacing: 2px; font-family: monospace; font-weight: bold; }
    .ritardo-testo { color: #e53e3e; font-size: 0.85em; font-weight: bold; }
    .dna-testo   { color: #8e44ad; font-size: 0.85em; font-weight: bold; }
    .streak-testo, .andata-testo, .mot-testo {
        font-size: 0.85em; font-weight: bold; padding: 3px 8px;
        border-radius: 5px; display: inline-block; margin-top: 5px; margin-right: 5px; }
    .streak-testo { color: #e74c3c; background-color: #fceae9; border: 1px solid #fadbd8; }
    .andata-testo { color: #2980b9; background-color: #ebf5fb; border: 1px solid #d6eaf8; }
    .mot-testo   { color: #1a1a1a; background-color: #fcf3cf; border: 1px solid #f1c40f; }
    .orario-match { color: #e67e22; font-weight: bold; font-family: monospace; font-size: 1.1em; }
    .quota-badge      { background-color: #2ecc71; padding: 3px 8px; border-radius: 4px;
        font-size: 0.85em; color: #ffffff; margin-left: 5px; font-weight: bold; }
    .quota-badge-calc { background-color: #95a5a6; padding: 3px 8px; border-radius: 4px;
        font-size: 0.85em; color: #ffffff; margin-left: 5px; }
    .value-positive { background-color: #27ae60; padding: 3px 8px; border-radius: 4px;
        font-size: 0.85em; color: #ffffff; margin-left: 5px; font-weight: bold; }
    .value-neutral  { background-color: #e67e22; padding: 3px 8px; border-radius: 4px;
        font-size: 0.85em; color: #ffffff; margin-left: 5px; }
    .pure-1x2 { margin-top: 15px; margin-bottom: 15px; padding: 10px;
        background-color: #fdfaf0; border-radius: 8px; border-left: 5px solid #f1c40f;
        font-size: 1.05em; }
    .star-testo  { color: #c0392b; font-weight: bold; font-size: 0.85em; }
    .h2h-details { font-size: 0.75em; color: #555; margin-top: 8px; padding: 8px;
        background-color: #f8f9fa; border-radius: 5px; border-left: 3px solid #8e44ad; }
    .stats-box   { background-color: #f4f6f7; padding: 12px; border-radius: 8px;
        border-left: 4px solid #3498db; margin-top: 10px; font-size: 0.9em; }
    .cs-testo    { color: #27ae60; font-weight: bold; }
    .fts-testo   { color: #c0392b; font-weight: bold; }
    .budget-tag  { font-size: 1.1em; font-weight: bold; color: #2c3e50; margin-bottom: 10px;
        display: inline-block; padding: 5px 10px; background-color: #ecf0f1;
        border-radius: 5px; border-left: 4px solid #34495e; }
    .kelly-tag   { font-size: 0.9em; color: #8e44ad; font-weight: bold;
        background-color: #f5f0ff; padding: 3px 8px; border-radius: 4px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# ⚙️ CONFIGURAZIONE
# ==========================================
API_KEY_FOOTBALL = 'dc4d6488653c2d9a763290a44eb1613f'
STAGIONE = "2025"
HEADERS = {'x-apisports-key': API_KEY_FOOTBALL}

# Cap xG: evita distribuzioni di Poisson assurde con moltiplicatori in cascata
XG_MAX = 3.2
XG_MIN = 0.10

# Margine bookmaker realistico per quote calibrate (~7%)
MARGINE_BOOKMAKER = 0.93

MASTER_LEAGUES = {
    "🇪🇺 Champions League":      2,
    "🇪🇺 Europa League":         3,
    "🇪🇺 Conference League":     848,
    "🇮🇹 Serie A":               135,
    "🇮🇹 Serie B":               136,
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League":      39,
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Championship":        40,
    "🇪🇸 La Liga":               140,
    "🇩🇪 Bundesliga":            78,
    "🇫🇷 Ligue 1":               61,
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 League One":         41,
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 League Two":         42,
    "🇳🇱 Eerste Divisie":        89,
    "🇩🇪 2. Bundesliga":         79,
    "🇪🇸 La Liga 2":             141,
    "🇳🇱 Eredivisie":            88,
    "🇵🇹 Primeira Liga":         94,
    "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Prem.":      281,
    "🇹🇷 Süper Lig":             203,
    "🇧🇪 Pro League":            144,
    "🇬🇷 Super League":          197,
    "🇸🇪 Allsvenskan":           113,
    "🇳🇴 Eliteserien":           69,
    "🇫🇮 Veikkausliiga":         244,
    "🇩🇰 Superliga":             119,
    "🇨🇭 Super League":          207,
    "🇦🇹 Bundesliga":            218,
    "🇸🇦 Saudi Pro League":      307,
    "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Championship": 284,
    "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish League One":  285,
}

COPPE_EUROPEE = {"🇪🇺 Champions League", "🇪🇺 Europa League", "🇪🇺 Conference League"}
LEGHE_ESTIVE  = {"🇸🇪 Allsvenskan", "🇳🇴 Eliteserien", "🇫🇮 Veikkausliiga"}
LEGHE_CIECHE  = {41, 42}   # League One/Two: radar infortuni offline

# ==========================================
# 🕵️ AUTO-DISCOVERY ID LEGA
# ==========================================
@st.cache_data(ttl=86400)
def trova_vero_id_lega(nazione: str, nome: str, fallback_id: int) -> int:
    try:
        resp = requests.get(
            "https://v3.football.api-sports.io/leagues",
            headers=HEADERS,
            params={'country': nazione, 'name': nome},
            timeout=5
        ).json()
        if resp.get('response'):
            return resp['response'][0]['league']['id']
    except Exception:
        pass
    return fallback_id

MASTER_LEAGUES["🇳🇴 Eliteserien"] = trova_vero_id_lega("Norway", "Eliteserien", 69)

# ==========================================
# 📡 MODULI API
# ==========================================
@st.cache_data(ttl=3600)
def get_active_leagues(start_date, end_date):
    active_ids = set()
    delta = end_date - start_date
    days = min(delta.days + 1, 7)
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
    """Ritorna (posizione, gol, assist, rating_medio, minuti_totali)."""
    if not player_id:
        return "Unknown", 0, 0, 6.0, 0
    try:
        resp = requests.get(
            "https://v3.football.api-sports.io/players",
            headers=HEADERS, params={'id': player_id, 'season': season}, timeout=8
        ).json()
        if resp.get('response'):
            stats_array = resp['response'][0]['statistics']
            pos = "Unknown"
            tot_mins, tot_goals, tot_assists = 0, 0, 0
            ratings = []
            for stat in stats_array:
                if pos == "Unknown" and stat['games'].get('position'):
                    pos = stat['games']['position']
                tot_mins    += stat['games'].get('minutes')  or 0
                tot_goals   += stat['goals'].get('total')    or 0
                tot_assists += stat['goals'].get('assists')  or 0
                if stat['games'].get('rating'):
                    ratings.append(float(stat['games']['rating']))
            avg_rating = sum(ratings) / len(ratings) if ratings else 6.0
            return pos, tot_goals, tot_assists, avg_rating, tot_mins
    except Exception:
        pass
    return "Unknown", 0, 0, 6.0, 0

def analizza_infortuni_pesati_v90(inf_list: list, season_lega: str):
    """
    Calcola malus attacco e boost difesa avversaria basandosi su
    minuti giocati e rating individuali (agnostico dalla lega).
    """
    malus_att = 0.0
    boost_opp = 0.0
    t1_star, t2_rot, t3_ris = 0, 0, 0
    squalificati, difensori_out = 0, 0
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

        if is_star:
            t1_star += 1
        elif mins >= 400:
            t2_rot += 1
        else:
            t3_ris += 1

        if gol >= 5 or assist >= 5 or (pos in ["Attacker", "Midfielder"] and is_star):
            malus_att += 0.15
            if gol >= 10:    malus_att += 0.10
            if assist >= 8:  malus_att += 0.10
            if rating >= 7.3: malus_att += 0.10

        if pos == "Defender":
            if is_star:
                boost_opp += 0.15
                difensori_out += 1
            elif mins >= 400:
                boost_opp += 0.05
                difensori_out += 1
        elif pos == "Goalkeeper" and is_star:
            portiere_titolare_out = True
            boost_opp += 0.25

    if difensori_out >= 2:
        boost_opp += 0.20

    return (
        min(0.60, malus_att),
        min(0.60, boost_opp),
        t1_star, t2_rot, t3_ris,
        len(visti), squalificati,
        portiere_titolare_out, difensori_out
    )

@st.cache_data(ttl=3600)
def scarica_quote_native(league_id: int, date_str: str, season_lega):
    try:
        resp = requests.get(
            "https://v3.football.api-sports.io/odds",
            headers=HEADERS,
            params={'league': league_id, 'season': season_lega, 'date': date_str, 'bookmaker': 8},
            timeout=8
        ).json()
        quote_dict = {}
        for item in resp.get('response', []):
            fix_id = item['fixture']['id']
            quote_dict[fix_id] = {}
            if item['bookmakers']:
                for bet in item['bookmakers'][0]['bets']:
                    if bet['id'] == 1:
                        for val in bet['values']:
                            if val['value'] == 'Home':      quote_dict[fix_id]['1'] = float(val['odd'])
                            elif val['value'] == 'Draw':    quote_dict[fix_id]['X'] = float(val['odd'])
                            elif val['value'] == 'Away':    quote_dict[fix_id]['2'] = float(val['odd'])
                    elif bet['id'] == 5:
                        for val in bet['values']:
                            label = val['value']
                            if "Over" in label:  quote_dict[fix_id][f"O{label.split(' ')[1]}"] = float(val['odd'])
                            elif "Under" in label: quote_dict[fix_id][f"U{label.split(' ')[1]}"] = float(val['odd'])
                    elif bet['id'] == 12:
                        for val in bet['values']:
                            if val['value'] == 'Home/Draw': quote_dict[fix_id]['1X'] = float(val['odd'])
                            elif val['value'] == 'Draw/Away': quote_dict[fix_id]['X2'] = float(val['odd'])
                            elif val['value'] == 'Home/Away': quote_dict[fix_id]['12'] = float(val['odd'])
                    elif bet['id'] == 6:
                        for val in bet['values']:
                            if val['value'] == 'Yes':  quote_dict[fix_id]['Goal']   = float(val['odd'])
                            elif val['value'] == 'No': quote_dict[fix_id]['NoGoal'] = float(val['odd'])
        return quote_dict
    except Exception:
        return {}

@st.cache_data(ttl=86400)
def analizza_statistiche_stagionali(league_id: int, team_id: int, season_lega):
    """Ritorna (clean_sheet%, failed_to_score%) sulla stagione."""
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
        cs_perc  = (stats.get('clean_sheet', {}).get('total', 0) / giocate) * 100
        fts_perc = (stats.get('failed_to_score', {}).get('total', 0) / giocate) * 100
        return cs_perc, fts_perc
    except Exception:
        return 0.0, 0.0

# FIX #5: Aggiunto @st.cache_data — prima mancava e causava 11 chiamate per partita
@st.cache_data(ttl=1800)
def analizza_statistiche_avanzate_pro(team_id: int):
    """
    Analisi avanzata ultime 10 partite.
    FIX: ora è cached (ttl=1800s). Riduce le chiamate API di ~80%.
    """
    try:
        resp = requests.get(
            "https://v3.football.api-sports.io/fixtures",
            headers=HEADERS, params={'team': team_id, 'last': 10, 'status': 'FT'}, timeout=8
        ).json()
        matches = resp.get('response', [])

        tot_poss, tot_tiri, tot_tiri_area, tot_gol_fatti = 0, 0, 0, 0
        tot_gol_subiti, tot_corner, tot_cart, tot_falli, tot_parate = 0, 0, 0, 0, 0
        match_v_stats = 0
        match_v_goals = 0
        squalificati_certi = 0

        for i, m in enumerate(matches):
            fix_id = m['fixture']['id']
            is_home = str(m['teams']['home']['id']) == str(team_id)

            gf = m['goals']['home'] if is_home else m['goals']['away']
            gs = m['goals']['away'] if is_home else m['goals']['home']
            if gf is not None and gs is not None:
                tot_gol_fatti  += int(gf)
                tot_gol_subiti += int(gs)
                match_v_goals  += 1

            # Controllo rossi solo sull'ultima partita
            if i == 0:
                events_resp = requests.get(
                    "https://v3.football.api-sports.io/fixtures/events",
                    headers=HEADERS, params={'fixture': fix_id}, timeout=8
                ).json()
                if events_resp.get('response'):
                    for ev in events_resp['response']:
                        if str(ev['team']['id']) == str(team_id) and ev['type'] == 'Card' and 'Red' in ev.get('detail', ''):
                            squalificati_certi += 1

            stats_resp = requests.get(
                "https://v3.football.api-sports.io/fixtures/statistics",
                headers=HEADERS, params={'fixture': fix_id}, timeout=8
            ).json()
            if stats_resp.get('response'):
                for t_stats in stats_resp['response']:
                    if str(t_stats['team']['id']) == str(team_id):
                        s = {s['type']: s['value'] for s in t_stats['statistics']}
                        poss = str(s.get('Ball Possession', '50%')).replace('%', '')
                        tot_poss       += int(poss) if poss.isdigit() else 50
                        tot_tiri       += int(s.get('Shots on Goal', 0)   or 0)
                        tot_tiri_area  += int(s.get('Shots insidebox', 0) or 0)
                        tot_corner     += int(s.get('Corner Kicks', 0)    or 0)
                        tot_falli      += int(s.get('Fouls', 0)           or 0)
                        tot_parate     += int(s.get('Goalkeeper Saves', 0)or 0)
                        tot_cart       += int(s.get('Yellow Cards', 0)    or 0) + int(s.get('Red Cards', 0) or 0)
                        match_v_stats  += 1

        if match_v_stats == 0: match_v_stats = 1
        if match_v_goals == 0: match_v_goals = 1

        avg_poss       = tot_poss       / match_v_stats
        avg_tiri       = tot_tiri       / match_v_stats
        avg_tiri_area  = tot_tiri_area  / match_v_stats
        avg_corner     = tot_corner     / match_v_stats
        avg_cart       = tot_cart       / match_v_stats
        avg_falli      = tot_falli      / match_v_stats
        avg_parate     = tot_parate     / match_v_stats
        avg_gf         = tot_gol_fatti  / match_v_goals
        avg_gs         = tot_gol_subiti / match_v_goals

        tiri_per_gol = avg_tiri / avg_gf if avg_gf > 0 else 10.0

        if avg_poss > 55 and avg_tiri_area < 4:
            stile = "Tiki-Taka Sterile"
        elif avg_poss < 45 and avg_tiri_area > 4:
            stile = "Verticale Diretto"
        else:
            stile = "Bilanciato"

        return (avg_poss, avg_tiri, avg_tiri_area, tiri_per_gol,
                avg_corner, avg_cart, avg_falli, avg_parate,
                stile, squalificati_certi, avg_gf, avg_gs)

    except Exception:
        return 50.0, 4.0, 5.0, 5.0, 4.5, 2.0, 10.0, 2.5, "Bilanciato", 0, 1.0, 1.0

# ==========================================
# 💰 QUOTA & VALUE BET
# ==========================================
def get_quota_finale(tip: str, prob: float, quote_reali: dict):
    """
    FIX #6: Usa margine bookmaker realistico (~7%) invece di 1.55x arbitrario.
    Ritorna (quota, is_reale).
    """
    if quote_reali and tip in quote_reali:
        return quote_reali[tip], True
    if prob <= 0:
        return 99.0, False
    quota_fair = 100.0 / prob
    quota_calibrata = quota_fair * MARGINE_BOOKMAKER   # -7% di margine
    return max(1.01, round(quota_calibrata, 2)), False

def calcola_value(prob_calc: float, quota: float) -> float:
    """
    NUOVO: Value Bet Index.
    Valore atteso = prob_stimata * quota.
    >1.0 → edge positivo (valore sulla scommessa).
    <1.0 → edge negativo (bookmaker avvantaggiato).
    """
    return (prob_calc / 100.0) * quota

def calcola_edge_pct(prob_calc: float, quota: float) -> float:
    """Edge percentuale: (EV - 1) * 100. Es: +8.5 significa +8.5% di vantaggio."""
    return (calcola_value(prob_calc, quota) - 1.0) * 100.0

def kelly_fraction(prob: float, quota: float, frazione: float = 0.25) -> float:
    """
    NUOVO: Kelly Criterion parziale (default 25%).
    Calcola la percentuale ottimale del bankroll da puntare.
    Ritorna 0 se il value è negativo (non scommettere).
    """
    p = prob / 100.0
    q = 1.0 - p
    b = quota - 1.0
    if b <= 0:
        return 0.0
    k = (b * p - q) / b
    return max(0.0, k * frazione)

# ==========================================
# 📊 CALCOLO MERCATI (POISSON)
# ==========================================
def calcola_prob_poisson(xg: float, gol: int) -> float:
    return ((xg ** gol) * math.exp(-xg)) / math.factorial(gol)

def calcola_tutti_i_mercati(xg_c: float, xg_t: float,
                             avg_corner_match: float, avg_cart_match: float,
                             is_sev: bool, tot_falli_match: float) -> dict:
    """
    FIX #2: Combo calcolate con probabilità congiunta corretta (entrambe divise per 100).
    FIX #3: HT/FT normalizzato correttamente.
    FIX #7: xG già cappato a XG_MAX prima di questa chiamata.
    """
    p = {
        "1": 0, "X": 0, "2": 0,
        "1X": 0, "X2": 0, "12": 0,
        "Goal": 0, "NoGoal": 0,
        "Pari": 0, "Dispari": 0
    }
    mg = {"MG 1-3": 0, "MG 1-4": 0, "MG 2-3": 0, "MG 2-4": 0, "MG 2-5": 0, "MG 3-4": 0}
    uo_lines = [1.5, 2.5, 3.5, 4.5]
    for line in uo_lines:
        p[f"U{line}"] = 0
        p[f"O{line}"] = 0
    p["Casa O0.5"]   = 0
    p["Ospite O0.5"] = 0

    re_prob = {}

    for gc in range(8):
        for gt in range(8):
            prob = calcola_prob_poisson(xg_c, gc) * calcola_prob_poisson(xg_t, gt) * 100.0
            tot  = gc + gt

            if   gc > gt: p["1"] += prob
            elif gc == gt: p["X"] += prob
            else:          p["2"] += prob

            if gc > 0 and gt > 0: p["Goal"]   += prob
            else:                  p["NoGoal"] += prob

            if tot % 2 == 0: p["Pari"]    += prob
            else:             p["Dispari"] += prob

            for line in uo_lines:
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

    # Correzione GG/NG in base a xG estremi
    if xg_c > 1.2 and xg_t > 1.2:
        p["Goal"]   = min(90.0, p["Goal"] * 1.18)
        p["NoGoal"] = max(10.0, 100.0 - p["Goal"])
    elif xg_c < 0.9 and xg_t < 0.9:
        p["NoGoal"] = min(90.0, p["NoGoal"] * 1.15)
        p["Goal"]   = max(10.0, 100.0 - p["NoGoal"])

    # FIX #2: Combo — probabilità congiunta corretta: (p1/100) * (p2/100) * 100
    combos = {
        "1X + Over 1.5":  (p["1X"]   / 100) * (p["O1.5"] / 100) * 100 * 0.92,
        "X2 + Over 1.5":  (p["X2"]   / 100) * (p["O1.5"] / 100) * 100 * 0.92,
        "1X + Under 3.5": (p["1X"]   / 100) * (p["U3.5"] / 100) * 100 * 0.95,
        "X2 + Under 3.5": (p["X2"]   / 100) * (p["U3.5"] / 100) * 100 * 0.95,
        "1 + Over 2.5":   (p["1"]    / 100) * (p["O2.5"] / 100) * 100 * 0.90,
        "2 + Over 2.5":   (p["2"]    / 100) * (p["O2.5"] / 100) * 100 * 0.90,
        "Goal + Over 2.5":(p["Goal"] / 100) * (p["O2.5"] / 100) * 100 * 0.95,
    }

    # FIX #3: HT/FT — normalizzazione corretta
    # ht_prob viene normalizzato a somma=1 (probabilità decimali)
    ht_raw = {"1": p["1"] * 0.9, "X": p["X"] * 1.5, "2": p["2"] * 0.9}
    tot_ht = sum(ht_raw.values())
    ht_prob = {k: v / tot_ht for k, v in ht_raw.items()}   # decimali (somma=1)

    htft = {}
    for ht in ["1", "X", "2"]:
        for ft in ["1", "X", "2"]:
            # ht_prob[ht] è già decimale, p[ft] è percentuale → dividiamo per 100
            htft[f"HT/FT {ht}/{ft}"] = ht_prob[ht] * (p[ft] / 100.0) * 100.0

    prob_corner_85 = min(92.0, max(15.0, (avg_corner_match / 9.5) * 55))
    tension = avg_cart_match + (1.5 if is_sev else 0) + (tot_falli_match / 20.0)
    prob_cart_45   = min(88.0, max(20.0, (tension / 5.0) * 55))

    special = {
        "Over 8.5 Angoli":     prob_corner_85,
        "Over 4.5 Cartellini": prob_cart_45,
    }

    return {**p, **mg, **re_prob, **combos, **htft, **special}

# ==========================================
# 🔎 ANALISI SQUADRA & H2H
# ==========================================
@st.cache_data(ttl=3600)
def analizza_squadra_globale(team_id: int):
    try:
        resp = requests.get(
            "https://v3.football.api-sports.io/fixtures",
            headers=HEADERS, params={'team': team_id, 'last': 10, 'status': 'FT'}, timeout=8
        ).json()
        matches = resp.get('response', [])
        if not matches:
            return 1.0, False, "N/D", 1.0, "Nessuno"

        ultima_data = datetime.strptime(matches[0]['fixture']['date'][:10], '%Y-%m-%d')
        diff_giorni = (datetime.now() - ultima_data).days
        is_stanca   = diff_giorni <= 4
        m_stanchezza = 0.95 if is_stanca else 1.0

        forma_str, punti = "", 0
        for m in matches[:5]:
            is_home = str(m['teams']['home']['id']) == str(team_id)
            gh, ga  = m['goals']['home'], m['goals']['away']
            if gh == ga:
                forma_str += "D"; punti += 1
            elif (is_home and gh > ga) or (not is_home and ga > gh):
                forma_str += "W"; punti += 3
            else:
                forma_str += "L"
        forma_str = forma_str[::-1]
        m_forma = 0.9 + (punti / 15) * 0.2

        stats = {'W': 0, 'D': 0, 'L': 0, 'Over': 0, 'Goal': 0}
        for m in matches:
            is_home = str(m['teams']['home']['id']) == str(team_id)
            gh, ga  = m['goals']['home'], m['goals']['away']
            if gh is not None and ga is not None:
                if gh == ga: stats['D'] += 1
                elif (is_home and gh > ga) or (not is_home and ga > gh): stats['W'] += 1
                else: stats['L'] += 1
                if (gh + ga) > 2: stats['Over'] += 1
                if gh > 0 and ga > 0: stats['Goal'] += 1

        ritardi = []
        if stats['D'] == 0:    ritardi.append("X")
        if stats['W'] == 0:    ritardi.append("Vittoria")
        if stats['Over'] == 0: ritardi.append("Over 2.5")
        if stats['Goal'] == 0: ritardi.append("Goal")

        return m_stanchezza, is_stanca, forma_str, m_forma, (", ".join(ritardi) if ritardi else "Nessuno")
    except Exception:
        return 1.0, False, "N/D", 1.0, "Nessuno"

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

        vittorie_c, vittorie_t, gol_c, gol_t = 0, 0, 0, 0
        andata_msg, boost_andata_c, boost_andata_t = "", 1.0, 1.0

        dettagli_list = []
        for m in matches:
            if m['goals']['home'] is not None:
                d_m = datetime.strptime(m['fixture']['date'][:10], '%Y-%m-%d').strftime('%d/%m/%Y')
                dettagli_list.append(
                    f"📅 {d_m}: {m['teams']['home']['name']} "
                    f"<b>{m['goals']['home']} - {m['goals']['away']}</b> "
                    f"{m['teams']['away']['name']}"
                )
        dettagli_str = "<br>".join(dettagli_list) if dettagli_list else "Nessun dato."

        ultimo_match = matches[0]
        data_ultimo  = datetime.strptime(ultimo_match['fixture']['date'][:10], '%Y-%m-%d')
        if (datetime.now() - data_ultimo).days <= 28:
            is_home_last  = ultimo_match['teams']['home']['id'] == id_casa
            gc_last, gt_last = ultimo_match['goals']['home'], ultimo_match['goals']['away']
            if gc_last is not None and gt_last is not None:
                g_c_and = gc_last if is_home_last else gt_last
                g_t_and = gt_last if is_home_last else gc_last
                diff = g_c_and - g_t_and
                andata_msg = f"🏆 Andata: {g_c_and} - {g_t_and}"
                if diff in [-1, -2]:
                    boost_andata_c = 1.25; andata_msg += " (Casa all'assalto ⚔️)"
                elif diff in [1, 2]:
                    boost_andata_t = 1.25; andata_msg += " (Ospiti all'assalto ⚔️)"
                elif diff <= -3 or diff >= 3:
                    boost_andata_c = 0.85; boost_andata_t = 0.85
                    andata_msg += " (Qualificazione chiusa 🛡️)"

        for m in matches:
            if m['goals']['home'] is None: continue
            is_home_now = m['teams']['home']['id'] == id_casa
            gc = m['goals']['home'] if is_home_now else m['goals']['away']
            gt = m['goals']['away'] if is_home_now else m['goals']['home']
            gol_c += gc; gol_t += gt
            if gc > gt: vittorie_c += 1
            elif gt > gc: vittorie_t += 1

        m_count = max(1, len([m for m in matches if m['goals']['home'] is not None]))
        tot_gol_h2h = max(1, gol_c + gol_t)
        m_h2h_c = min(1.20, max(0.80,
            0.90 + (vittorie_c / m_count) * 0.20 + (gol_c / (m_count * tot_gol_h2h)) * 0.10))
        m_h2h_t = min(1.20, max(0.80,
            0.90 + (vittorie_t / m_count) * 0.20 + (gol_t / (m_count * tot_gol_h2h)) * 0.10))

        storico_str = f"Vittorie: 🏠 {vittorie_c} - {vittorie_t} ✈️ | Gol H2H: {gol_c} a {gol_t}"
        return (m_h2h_c, m_h2h_t, gol_c, gol_t, storico_str,
                boost_andata_c, boost_andata_t, andata_msg, dettagli_str)
    except Exception:
        return 1.0, 1.0, 0, 0, "Dati N/D", 1.0, 1.0, "", "Nessun dato."

@st.cache_data(ttl=3600)
def scarica_meteo(citta: str):
    try:
        resp = requests.get(f"https://wttr.in/{citta}?format=j1", timeout=3).json()
        cond  = resp['current_condition'][0]['weatherDesc'][0]['value']
        pioggia = any(p in cond.lower() for p in ['rain', 'snow', 'shower', 'thunder'])
        return (0.90, f"🌧️ {cond}") if pioggia else (1.0, f"☀️ {cond}")
    except Exception:
        return 1.0, "🌥️ Dato N/D"

# ==========================================
# 🏗️ UTILITY
# ==========================================
def semplifica_nome(nome: str) -> str:
    """
    FIX #11: Sostituzioni più conservative per evitare mismatch nel database.
    Solo suffissi/prefissi interi con spazio, non substring interne.
    """
    for token in [' FC', ' AC', ' BC', ' AS', ' Calcio', ' AFC', ' SL']:
        nome = nome.replace(token, '')
    for token in ['FC ', 'AC ', 'AS ', 'AFC ', 'SL ']:
        if nome.startswith(token):
            nome = nome[len(token):]
    return nome.strip()

def get_family(tip: str) -> str:
    if tip in ["1", "X", "2", "1X", "X2", "12"]:        return "1X2"
    if ("U" in tip or "O" in tip) and "+" not in tip \
        and "Casa" not in tip and "Ospite" not in tip \
        and "Angoli" not in tip and "Cartellini" not in tip: return "UO"
    if "MG" in tip:                                       return "MG"
    if "Goal" in tip or "NoGoal" in tip:                  return "GGNG"
    if "+" in tip:                                        return "COMBO"
    if "Risultato" in tip:                                return "RE"
    if "HT/FT" in tip:                                   return "HTFT"
    if tip in ["Pari", "Dispari"]:                        return "PD"
    if "Angoli" in tip or "Cartellini" in tip:            return "SPECIAL"
    return "ALTRO"

def costruisci_schedina_dinamica(pool: list, min_q: float, max_q: float,
                                  target_mult: float, escludi_match=None,
                                  max_match_q: float = 5.0, max_righe: int = 12,
                                  max_same_family: int = 2):
    if escludi_match is None:
        escludi_match = set()

    valid = [x for x in pool
             if min_q <= float(x['Quota']) <= max_q
             and float(x['Quota']) <= max_match_q
             and float(x.get('Edge', 0)) > -15]   # scarta scommesse con edge peggiore di -15%

    # Ordina per value bet (EV) decrescente
    pool_ordinata = sorted(valid,
                           key=lambda x: calcola_value(x['Prob'], float(x['Quota'])),
                           reverse=True)

    selezionate, viste_locali, family_counts = [], set(), {}
    q_tot, prob_tot = 1.0, 1.0

    for item in pool_ordinata:
        famiglia   = get_family(item['Tip'])
        match_name = item['Match']
        if (match_name not in viste_locali
                and match_name not in escludi_match
                and family_counts.get(famiglia, 0) < max_same_family):
            selezionate.append(item)
            viste_locali.add(match_name)
            family_counts[famiglia] = family_counts.get(famiglia, 0) + 1
            q_tot    *= float(item['Quota'])
            prob_tot *= (item['Prob'] / 100.0)

        if q_tot >= target_mult or len(selezionate) >= max_righe:
            break

    return selezionate, q_tot, prob_tot, viste_locali.union(escludi_match)

# ==========================================
# 🏠 STATO & SIDEBAR
# ==========================================
if 'data_master'      not in st.session_state: st.session_state.data_master      = {}
if 'all_tips_global'  not in st.session_state: st.session_state.all_tips_global  = []

st.sidebar.header("⚙️ Centrale Operativa V90")

date_range = st.sidebar.date_input("Seleziona Periodo (Dal - Al):", [])
if len(date_range) == 2:   start_date, end_date = date_range[0], date_range[1]
elif len(date_range) == 1: start_date = end_date = date_range[0]
else:                       start_date = end_date = datetime.now().date()

start_str = start_date.strftime('%Y-%m-%d')
end_str   = end_date.strftime('%Y-%m-%d')

st.sidebar.markdown("---")
budget_totale = st.sidebar.number_input(
    "💰 Budget Totale da Investire (€):", min_value=5.0, value=50.0, step=5.0)
st.sidebar.markdown("---")

if st.sidebar.button("🗑️ SVUOTA MEMORIA V90 (Hard Reset)"):
    st.cache_data.clear()
    st.session_state.data_master     = {}
    st.session_state.all_tips_global = []
    st.sidebar.success("✅ Cache svuotata!")
st.sidebar.markdown("---")

with st.sidebar:
    if st.button("🔍 Trova Campionati Attivi nel Periodo"):
        with st.spinner("Scansione palinsesto..."):
            st.session_state['active_leagues'] = get_active_leagues(start_date, end_date)

if 'active_leagues' not in st.session_state:
    st.session_state['active_leagues'] = MASTER_LEAGUES

active_dict = st.session_state['active_leagues']
if not active_dict:
    st.sidebar.warning("Nessun campionato supportato attivo.")

scelte    = st.sidebar.multiselect(
    "Campionati in campo:", list(active_dict.keys()), default=list(active_dict.keys()))
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
        f_id = active_dict[name]
        is_coppa         = name in COPPE_EUROPEE
        is_lega_estiva   = name in LEGHE_ESTIVE
        is_lega_cieca    = f_id in LEGHE_CIECHE
        stagione_lega    = start_date.year if is_lega_estiva else STAGIONE

        with st.spinner(f"Analisi V90 {name}..."):
            fix = requests.get(
                "https://v3.football.api-sports.io/fixtures",
                headers=HEADERS,
                params={'league': f_id, 'season': stagione_lega,
                        'from': start_str, 'to': end_str},
                timeout=10
            ).json()
            std = requests.get(
                "https://v3.football.api-sports.io/standings",
                headers=HEADERS,
                params={'league': f_id, 'season': stagione_lega},
                timeout=10
            ).json()

            if not fix.get('response'):
                continue

            db_stats: dict = {}
            # FIX #9: punti champions e salvezza estratti dalla classifica reale
            punti_champions     = 0
            punti_salvezza      = 0
            tot_squadre         = 20
            partite_tot_camp    = 38

            if (std.get('response')
                    and len(std['response']) > 0
                    and 'league' in std['response'][0]
                    and 'standings' in std['response'][0]['league']):

                tutti_i_gironi = std['response'][0]['league']['standings']
                for gruppo in tutti_i_gironi:
                    tot_squadre   = len(gruppo)
                    partite_tot_camp = max(
                        (tot_squadre - 1) * 2, 38)   # formula round-robin

                    # FIX #9: estrai i punti reali dei posti-chiave
                    if tot_squadre >= 4:
                        # 4° posto = ultimo posto Champions (in leghe a 4 slot)
                        punti_champions = gruppo[3]['points']
                        # Terzultimo = zona play-out/retrocessione
                        punti_salvezza  = gruppo[tot_squadre - 4]['points']

                    for t in gruppo:
                        n = semplifica_nome(t['team']['name'])
                        db_stats[n] = {
                            'id':      t['team']['id'],
                            'rank':    t['rank'],
                            'giocate': t['all']['played'],
                            'punti':   t['points'],
                            'ac': t['home']['goals']['for']     / max(1, t['home']['played']),
                            'dc': t['home']['goals']['against'] / max(1, t['home']['played']),
                            'at': t['away']['goals']['for']     / max(1, t['away']['played']),
                            'dt': t['away']['goals']['against'] / max(1, t['away']['played']),
                        }
            else:
                # Fallback: costruisci db_stats dalle partite in programma
                for f in fix['response']:
                    for tt in ['home', 'away']:
                        n    = semplifica_nome(f['teams'][tt]['name'])
                        t_id = f['teams'][tt]['id']
                        if n not in db_stats:
                            db_stats[n] = {
                                'id': t_id, 'rank': 10, 'giocate': 0, 'punti': 0,
                                'ac': 0.0, 'dc': 0.0, 'at': 0.0, 'dt': 0.0
                            }

            # Cache quote per giornata
            date_giocate = {f['fixture']['date'][:10] for f in fix['response']}
            odds_cache: dict = {}
            for d_match in date_giocate:
                odds_cache[d_match] = scarica_quote_native(f_id, d_match, stagione_lega)

            matches_list = []

            for f in fix['response']:
                status = f['fixture']['status']['short']
                if status in ['PST', 'CANC', 'ABD', 'AWD', 'WO']:
                    continue

                fix_id         = f['fixture']['id']
                match_date_str = f['fixture']['date'][:10]
                match_time_utc = datetime.fromisoformat(f['fixture']['date'])
                if match_time_utc <= now_utc:
                    continue
                match_time_ita = match_time_utc.astimezone(tz_ita)
                orario_ita     = match_time_ita.strftime('%d/%m %H:%M')

                c_u = f['teams']['home']['name']
                t_u = f['teams']['away']['name']
                c_s = semplifica_nome(c_u)
                t_s = semplifica_nome(t_u)

                # Playoff rescue
                if c_s not in db_stats:
                    db_stats[c_s] = {'id': f['teams']['home']['id'], 'rank': 10,
                                     'giocate': 0, 'punti': 0,
                                     'ac': 0.0, 'dc': 0.0, 'at': 0.0, 'dt': 0.0}
                if t_s not in db_stats:
                    db_stats[t_s] = {'id': f['teams']['away']['id'], 'rank': 10,
                                     'giocate': 0, 'punti': 0,
                                     'ac': 0.0, 'dc': 0.0, 'at': 0.0, 'dt': 0.0}

                quote_reali_match = odds_cache.get(match_date_str, {}).get(fix_id, {})

                # --- Dati squadra ---
                m_st_c, is_stanca_c, forma_c, m_f_c, rit_c = analizza_squadra_globale(db_stats[c_s]['id'])
                m_st_t, is_stanca_t, forma_t, m_f_t, rit_t = analizza_squadra_globale(db_stats[t_s]['id'])

                cs_c, fts_c = analizza_statistiche_stagionali(f_id, db_stats[c_s]['id'], stagione_lega)
                cs_t, fts_t = analizza_statistiche_stagionali(f_id, db_stats[t_s]['id'], stagione_lega)

                m_met, d_met = scarica_meteo(c_s)
                (m_h2h_c, m_h2h_t, gol_h2h_c, gol_h2h_t,
                 str_h2h, b_and_c, b_and_t,
                 andata_msg, dettagli_h2h_str) = analizza_h2h_dna_e_andata(
                    db_stats[c_s]['id'], db_stats[t_s]['id'])

                (poss_c, tiri_c, box_c, conv_c, corn_c, cart_c, falli_c,
                 parate_c, stile_c, sq_certi_c, gf_10_c, gs_10_c) = analizza_statistiche_avanzate_pro(db_stats[c_s]['id'])
                (poss_t, tiri_t, box_t, conv_t, corn_t, cart_t, falli_t,
                 parate_t, stile_t, sq_certi_t, gf_10_t, gs_10_t) = analizza_statistiche_avanzate_pro(db_stats[t_s]['id'])

                c_id = db_stats[c_s]['id']
                t_id = db_stats[t_s]['id']
                msg_radar = ("⚠️ Radar Infortuni Offline (Lega Minore) — Algoritmo 100% Statistico"
                             if is_lega_cieca else "")

                if is_lega_cieca:
                    malus_att_c = boost_opp_c = 0.0
                    t1_c = t2_c = t3_c = count_c = sq_c = def_out_c = 0
                    gk_out_c = False
                    malus_att_t = boost_opp_t = 0.0
                    t1_t = t2_t = t3_t = count_t = sq_t = def_out_t = 0
                    gk_out_t = False
                    if sq_certi_c > 0:
                        sq_c    += sq_certi_c; count_c += sq_certi_c
                        malus_att_c += 0.05 * sq_certi_c
                    if sq_certi_t > 0:
                        sq_t    += sq_certi_t; count_t += sq_certi_t
                        malus_att_t += 0.05 * sq_certi_t
                else:
                    inj_resp = requests.get(
                        "https://v3.football.api-sports.io/injuries",
                        headers=HEADERS, params={'fixture': fix_id}, timeout=8
                    ).json()
                    inf_all = inj_resp.get('response', [])
                    if not isinstance(inf_all, list): inf_all = []

                    if len(inf_all) == 0:
                        inj_fall_c = requests.get(
                            "https://v3.football.api-sports.io/injuries",
                            headers=HEADERS, params={'team': c_id, 'date': match_date_str}, timeout=8
                        ).json()
                        inj_fall_t = requests.get(
                            "https://v3.football.api-sports.io/injuries",
                            headers=HEADERS, params={'team': t_id, 'date': match_date_str}, timeout=8
                        ).json()
                        if isinstance(inj_fall_c.get('response'), list):
                            inf_all.extend(inj_fall_c['response'])
                        if isinstance(inj_fall_t.get('response'), list):
                            inf_all.extend(inj_fall_t['response'])

                    inf_c_list = [i for i in inf_all if str(i['team']['id']) == str(c_id)]
                    inf_t_list = [i for i in inf_all if str(i['team']['id']) == str(t_id)]

                    (malus_att_c, boost_opp_c, t1_c, t2_c, t3_c,
                     count_c, sq_c, gk_out_c, def_out_c) = analizza_infortuni_pesati_v90(inf_c_list, stagione_lega)
                    (malus_att_t, boost_opp_t, t1_t, t2_t, t3_t,
                     count_t, sq_t, gk_out_t, def_out_t) = analizza_infortuni_pesati_v90(inf_t_list, stagione_lega)

                    if sq_certi_c > 0 and sq_c == 0:
                        sq_c += sq_certi_c; count_c += sq_certi_c
                        malus_att_c += 0.05 * sq_certi_c
                    if sq_certi_t > 0 and sq_t == 0:
                        sq_t += sq_certi_t; count_t += sq_certi_t
                        malus_att_t += 0.05 * sq_certi_t

                # Squad Depth Buffer (Sindrome di Golia)
                if not is_coppa:
                    punti_c_depth = db_stats[c_s]['punti']
                    punti_t_depth = db_stats[t_s]['punti']
                    gap_c = punti_c_depth - punti_t_depth
                    gap_t = punti_t_depth - punti_c_depth
                    if gap_c >= 15:
                        ammortizzatore = max(0.20, 1.0 - (gap_c / 45.0))
                        malus_att_c  *= ammortizzatore
                        boost_opp_t  *= ammortizzatore
                    elif gap_t >= 15:
                        ammortizzatore = max(0.20, 1.0 - (gap_t / 45.0))
                        malus_att_t  *= ammortizzatore
                        boost_opp_c  *= ammortizzatore

                streak_breaker_c = (gol_h2h_c == 0) and (count_t > 0 or is_stanca_t)
                streak_breaker_t = (gol_h2h_t == 0) and (count_c > 0 or is_stanca_c)

                m_mot_c, m_mot_t, tension_idx = 1.0, 1.0, 1.0
                msg_mot = ""

                if is_coppa and mese_att in [3, 4, 5]:
                    m_mot_c = m_mot_t = 1.25
                    tension_idx += 0.3
                    msg_mot = "🔥 DENTRO O FUORI (Coppa)"
                elif not is_coppa:
                    punti_c  = db_stats[c_s]['punti']
                    punti_t  = db_stats[t_s]['punti']
                    rank_c   = db_stats[c_s]['rank']
                    rank_t   = db_stats[t_s]['rank']
                    gap_ch_c = punti_champions - punti_c
                    gap_ch_t = punti_champions - punti_t

                    # Casa
                    if rank_c <= 6 or (0 < gap_ch_c <= 7):
                        m_mot_c = 1.15; msg_mot += "🏆 C.Vertice "
                    elif rank_c >= tot_squadre - 6:
                        m_mot_c = 1.20; msg_mot += "🆘 C.Disperata "; tension_idx += 0.15
                    elif mese_att >= 3 and (punti_c - punti_salvezza) > 9 and gap_ch_c > 10:
                        m_mot_c = 1.10; msg_mot += "🌴 C.Sgombra "
                    else:
                        m_mot_c = 1.05

                    # Trasferta
                    if rank_t <= 6 or (0 < gap_ch_t <= 7):
                        m_mot_t = 1.15; msg_mot += "🏆 O.Vertice"
                    elif rank_t >= tot_squadre - 6:
                        m_mot_t = 1.20; msg_mot += "🆘 O.Disperata"; tension_idx += 0.15
                    elif mese_att >= 3 and (punti_t - punti_salvezza) > 9 and gap_ch_t > 10:
                        m_mot_t = 1.10; msg_mot += "🌴 O.Sgombra"
                    else:
                        m_mot_t = 1.05

                    if abs(rank_c - rank_t) <= 3:
                        tension_idx += 0.2

                # --- Hybrid xG Core ---
                xg_standings_c = math.sqrt(
                    max(0.01, db_stats[c_s]['ac']) * max(0.01, db_stats[t_s]['dt']))
                xg_standings_t = math.sqrt(
                    max(0.01, db_stats[t_s]['at']) * max(0.01, db_stats[c_s]['dc']))

                xg_momentum_c  = math.sqrt(max(0.01, gf_10_c) * max(0.01, gs_10_t))
                xg_momentum_t  = math.sqrt(max(0.01, gf_10_t) * max(0.01, gs_10_c))

                partite_casa   = db_stats[c_s]['giocate']
                peso_momentum  = 0.80 if (is_coppa or partite_casa <= 5) else 0.30
                peso_standings = 1.0 - peso_momentum

                xg_base_c = ((xg_standings_c * peso_standings) + (xg_momentum_c * peso_momentum)) * m_f_c * m_st_c
                xg_base_t = ((xg_standings_t * peso_standings) + (xg_momentum_t * peso_momentum)) * m_f_t * m_st_t

                # Malus per leghe basse-scoring
                malus_league = 0.85 if name in ["🇬🇷 Super League", "🇫🇷 Ligue 1", "🇮🇹 Serie B"] else 1.0
                xg_base_c   *= malus_league
                xg_base_t   *= malus_league

                # Efficienza realizzativa
                if conv_c < 3.0:   xg_base_c *= 1.15
                elif conv_c > 7.0: xg_base_c *= 0.85
                if conv_t < 3.0:   xg_base_t *= 1.15
                elif conv_t > 7.0: xg_base_t *= 0.85

                # Box dominance
                boost_box_c = min(1.20, 1.0 + (box_c / 15.0) * 0.15)
                boost_box_t = min(1.20, 1.0 + (box_t / 15.0) * 0.15)
                xg_base_c  *= boost_box_c
                xg_base_t  *= boost_box_t

                # Portiere avversario
                malus_port_c = min(0.25, (parate_c / 6.0) * 0.20)
                malus_port_t = min(0.25, (parate_t / 6.0) * 0.20)
                xg_base_c   *= (1 - malus_port_t)
                xg_base_t   *= (1 - malus_port_c)

                # Falli alti → partita spezzettata → meno gol
                tot_falli_match = falli_c + falli_t
                if tot_falli_match > 28:
                    xg_base_c *= 0.90
                    xg_base_t *= 0.90

                # Clean sheet / failed to score
                if fts_c > 35.0: xg_base_c *= 0.85
                if cs_t  > 35.0: xg_base_c *= 0.85
                if fts_t > 35.0: xg_base_t *= 0.85
                if cs_c  > 35.0: xg_base_t *= 0.85

                se_sgombra_c = "C.Sgombra" in msg_mot
                se_sgombra_t = "O.Sgombra" in msg_mot

                # Incrocio totale xG
                xg_c = (xg_base_c
                        * (1 - malus_att_c) * (1 + boost_opp_t)
                        * m_h2h_c * b_and_c * m_mot_c
                        * (1.10 if se_sgombra_t else 1.0))
                xg_t = (xg_base_t
                        * (1 - malus_att_t) * (1 + boost_opp_c)
                        * m_h2h_t * b_and_t * m_mot_t
                        * (1.10 if se_sgombra_c else 1.0))

                msg_streak = ""
                if streak_breaker_c:
                    xg_c *= 1.45; msg_streak += "🔥 STREAK CASA "
                if streak_breaker_t:
                    xg_t *= 1.45; msg_streak += "🔥 STREAK OSPITE"

                xg_c *= m_met; xg_t *= m_met

                arb    = f['fixture']['referee'] or "N/D"
                is_sev = any(s in str(arb) for s in
                             ["Orsato", "Maresca", "Taylor", "Oliver", "Lahoz", "Hernandez"])
                m_arb  = 1.05 if is_sev else 1.0
                xg_c  *= m_arb; xg_t *= m_arb

                # FIX #7: CAP xG prima di Poisson — evita distribuzioni assurde
                xg_c = min(XG_MAX, max(XG_MIN, xg_c))
                xg_t = min(XG_MAX, max(XG_MIN, xg_t))

                avg_corner_match = corn_c + corn_t
                avg_cart_match   = cart_c + cart_t

                full_tips = calcola_tutti_i_mercati(
                    xg_c, xg_t, avg_corner_match, avg_cart_match, is_sev, tot_falli_match)

                best_1x2_key = max(["1", "X", "2"], key=lambda k: full_tips[k])
                if full_tips[best_1x2_key] < 45.0:
                    best_1x2_key  = "No Segno Fisso"
                    best_1x2_prob = 0.0
                    best_1x2_q    = "-"
                    best_1x2_real = False
                else:
                    best_1x2_prob = full_tips[best_1x2_key]
                    best_1x2_q, best_1x2_real = get_quota_finale(
                        best_1x2_key, best_1x2_prob, quote_reali_match)

                for k, v in full_tips.items():
                    q_fin, is_real = get_quota_finale(k, v, quote_reali_match)
                    edge           = calcola_edge_pct(v, q_fin)
                    kelly          = kelly_fraction(v, q_fin)
                    st.session_state.all_tips_global.append({
                        "Match":  f"{c_u} vs {t_u}",
                        "League": name,
                        "Tip":    k,
                        "Prob":   v,
                        "Quota":  q_fin,
                        "Real":   is_real,
                        "Time":   orario_ita,
                        "Edge":   edge,
                        "Kelly":  kelly,
                    })

                matches_list.append({
                    "orario": orario_ita, "c_u": c_u, "t_u": t_u, "c_s": c_s, "t_s": t_s,
                    "rank_c": db_stats[c_s]['rank'], "rank_t": db_stats[t_s]['rank'],
                    "cs_c": cs_c, "fts_c": fts_c, "cs_t": cs_t, "fts_t": fts_t,
                    "all_tips": full_tips, "best_1x2": (best_1x2_key, best_1x2_prob, best_1x2_q, best_1x2_real),
                    "quote_reali": quote_reali_match,
                    "xg_c": xg_c, "xg_t": xg_t, "arb": arb, "is_sev": is_sev,
                    "count_c": count_c, "sq_c": sq_c, "t1_c": t1_c, "t2_c": t2_c,
                    "t3_c": t3_c, "gk_out_c": gk_out_c, "def_out_c": def_out_c,
                    "count_t": count_t, "sq_t": sq_t, "t1_t": t1_t, "t2_t": t2_t,
                    "t3_t": t3_t, "gk_out_t": gk_out_t, "def_out_t": def_out_t,
                    "meteo": d_met, "msg_radar": msg_radar,
                    "dna_h2h": str_h2h, "dettagli_h2h": dettagli_h2h_str,
                    "streak_msg": msg_streak.strip(), "andata_msg": andata_msg,
                    "msg_mot": msg_mot.strip(),
                    "stan_c": "⚠️ Fatigue" if is_stanca_c else "✅ Riposo",
                    "stan_t": "⚠️ Fatigue" if is_stanca_t else "✅ Riposo",
                    "forma_c": forma_c, "forma_t": forma_t, "rit_c": rit_c, "rit_t": rit_t,
                    "poss_c": poss_c, "tiri_c": tiri_c, "conv_c": conv_c, "stile_c": stile_c,
                    "box_c": box_c, "falli_c": falli_c, "parate_c": parate_c,
                    "poss_t": poss_t, "tiri_t": tiri_t, "conv_t": conv_t, "stile_t": stile_t,
                    "box_t": box_t, "falli_t": falli_t, "parate_t": parate_t,
                    "corn_tot": avg_corner_match, "cart_tot": avg_cart_match,
                    "falli_tot": tot_falli_match,
                })

            if matches_list:
                st.session_state.data_master[name] = matches_list

# ==========================================
# 🖥️ DISPLAY: 3 TAB
# ==========================================
if st.session_state.data_master:
    t1, t2, t3 = st.tabs(["🛒 TOP 10 & BUILDER", "🔬 ESPLORATORE PARTITE", "🏆 SCHEDINE AUTOMATICHE"])

    # ─── TAB 1: Builder ─────────────────────────────────────────────────────────
    with t1:
        st.header("🛒 BET BUILDER & CLASSIFICHE OMNI-MARKET")
        st.info("💡 **Value Bet Index**: Verde = edge positivo (scommessa con valore). "
                "Grigio = edge negativo. La colonna **Kelly%** indica la percentuale "
                "ottimale del budget da puntare su quella singola scommessa.")

        def mostra_tabella_interattiva(titolo: str, tip_filter, min_q: float = 1.01, max_rows: int = 10):
            st.subheader(titolo)
            pool = [x for x in st.session_state.all_tips_global
                    if (tip_filter(x['Tip']) if callable(tip_filter) else x['Tip'] in tip_filter)
                    and float(x['Quota']) >= min_q]
            if not pool:
                st.info("Nessun dato disponibile per questa categoria.")
                return []

            df = pd.DataFrame(pool).sort_values(by="Edge", ascending=False).head(max_rows)
            df = df[['Match', 'Tip', 'Prob', 'Quota', 'Edge', 'Kelly', 'Time', 'League']]
            df['Kelly'] = (df['Kelly'] * 100).round(1)   # in percentuale
            df.insert(0, "🛒", False)

            edited_df = st.data_editor(
                df,
                column_config={
                    "🛒":    st.column_config.CheckboxColumn("Seleziona", default=False),
                    "Prob":  st.column_config.NumberColumn("Probabilità (%)", format="%.1f%%"),
                    "Quota": st.column_config.NumberColumn("Quota",           format="%.2f"),
                    "Edge":  st.column_config.NumberColumn("Edge (%)",        format="%.1f%%"),
                    "Kelly": st.column_config.NumberColumn("Kelly (%)",        format="%.1f%%"),
                },
                hide_index=True,
                use_container_width=True,
                disabled=['Match', 'Tip', 'Prob', 'Quota', 'Edge', 'Kelly', 'Time', 'League'],
                key=f"editor_{titolo}"
            )
            return edited_df[edited_df["🛒"] == True].to_dict('records')

        sel_1   = mostra_tabella_interattiva(
            "👑 Top 10 Value Bet Assoluta",
            lambda tip: tip not in ["U4.5", "Casa O0.5", "Ospite O0.5"])
        sel_2   = mostra_tabella_interattiva("🛡️ Top 10 Doppie Chance",   ["1X", "X2", "12"])
        sel_3   = mostra_tabella_interattiva("⚽ Top 10 Over / Under",
            lambda tip: (tip.startswith("O") or tip.startswith("U")) and "+" not in tip)
        sel_4   = mostra_tabella_interattiva("🎯 Top 10 Goal / NoGoal",   ["Goal", "NoGoal"])
        sel_mg  = mostra_tabella_interattiva("🥅 Top 10 Multigol",        lambda tip: tip.startswith("MG"))
        sel_combo = mostra_tabella_interattiva("🧩 Top 10 Combo Match",    lambda tip: "+" in tip)
        sel_6   = mostra_tabella_interattiva(
            "🧨 Top 10 Azzardi (Quote >= 2.50)", lambda tip: True, min_q=2.50)

        tutte = sel_1 + sel_2 + sel_3 + sel_4 + sel_mg + sel_combo + sel_6
        viste: set = set()
        carrello: list = []
        for item in tutte:
            chiave = f"{item['Match']}_{item['Tip']}"
            if chiave not in viste:
                viste.add(chiave)
                carrello.append(item)

        st.markdown("---")
        st.markdown("<div class='strategy-box builder-bg'>", unsafe_allow_html=True)
        st.header("🧾 IL TUO CARRELLO")

        if carrello:
            q_tot_b, p_tot_b = 1.0, 1.0
            testo_scontrino = "=== RICEVUTA MATRIX V90 ===\n\n"

            for pick in carrello:
                edge_label = f"Edge: {pick['Edge']:.1f}%"
                st.write(
                    f"✅ {pick['Match']}: **{pick['Tip']}** "
                    f"(Q {pick['Quota']:.2f} | {edge_label} | "
                    f"Kelly: {pick['Kelly']*100:.1f}%)")
                q_tot_b  *= float(pick['Quota'])
                p_tot_b  *= float(pick['Prob']) / 100.0
                testo_scontrino += (
                    f"[{pick['Time']}] {pick['Match']} -> {pick['Tip']} "
                    f"@ {pick['Quota']:.2f} | Edge: {pick['Edge']:.1f}%\n")

            testo_scontrino += (
                f"\n📊 QUOTA TOTALE: {q_tot_b:.2f}\n"
                f"🎯 PROBABILITÀ CONGIUNTA: {p_tot_b*100:.2f}%\n"
                f"💰 VINCITA STIMATA (su {budget_totale}€): ~{budget_totale * q_tot_b:.2f}€\n")

            st.write("---")
            cb1, cb2, cb3 = st.columns(3)
            cb1.metric("Quota Totale",            f"{q_tot_b:.2f}")
            cb2.metric("Probabilità Congiunta",   f"{p_tot_b*100:.2f}%")
            cb3.metric(f"Vincita (Budget {budget_totale}€)", f"~{budget_totale * q_tot_b:.2f}€")

            st.download_button(
                label="💾 SCARICA / SALVA SCHEDINA (TXT)",
                data=testo_scontrino,
                file_name=f"Matrix_Ticket_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain"
            )
        else:
            st.info("👆 Spunta qualche partita dalle classifiche per costruire la schedina.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ─── TAB 2: Esploratore ──────────────────────────────────────────────────────
    with t2:
        st.write(f"Partite per il periodo **{start_str} / {end_str}**.")
        for camp, matches in st.session_state.data_master.items():
            with st.expander(f"🏆 {camp}", expanded=False):
                matches = sorted(matches, key=lambda x: x['orario'])
                for m in matches:
                    titolo_exp = (
                        f"🕒 {m['orario']} | 🏟️ {m['c_u']} vs {m['t_u']} | "
                        f"👑 Pick: {m['best_1x2'][0]}"
                        if m['best_1x2'][0] != "No Segno Fisso"
                        else f"🕒 {m['orario']} | 🏟️ {m['c_u']} vs {m['t_u']} | ⚠️ No Bet"
                    )
                    with st.expander(titolo_exp, expanded=False):

                        st.markdown(
                            f"<div style='font-size:0.85em; color:#7f8c8d; margin-bottom:10px;'>"
                            f"<b>Arbitro:</b> {m['arb']} | "
                            f"<b>VAR:</b> {'⚠️ Fiscale' if m['is_sev'] else '⚖️ Standard'} | "
                            f"<b>Clima:</b> {m['meteo']}</div>",
                            unsafe_allow_html=True)

                        if m.get('msg_radar'):
                            st.warning(m['msg_radar'])

                        tags_html = ""
                        if m['msg_mot']:    tags_html += f"<span class='mot-testo'>{m['msg_mot']}</span> "
                        if m['andata_msg']: tags_html += f"<span class='andata-testo'>{m['andata_msg']}</span> "
                        if m['streak_msg']: tags_html += f"<span class='streak-testo'>{m['streak_msg']}</span> "
                        if tags_html:
                            st.markdown(f"<div style='margin-bottom:15px;'>{tags_html}</div>",
                                        unsafe_allow_html=True)

                        st.markdown("### 🎯 PREVISIONI MATRIX V90")
                        pred_c1, pred_c2 = st.columns([1, 1.5])

                        with pred_c1:
                            if m['best_1x2'][0] == "No Segno Fisso":
                                st.markdown(
                                    "<div class='pure-1x2' style='text-align:center;'>"
                                    "⚠️ <b>NESSUN SEGNO SECCO SICURO</b><br>"
                                    "<span style='font-size:0.8em;'>Affidati alle Combo/Multigol</span>"
                                    "</div>", unsafe_allow_html=True)
                            else:
                                bc = "quota-badge" if m['best_1x2'][3] else "quota-badge-calc"
                                bl = "Ufficiale Bet365" if m['best_1x2'][3] else "Calibrata V90"
                                # Value del segno migliore
                                edge_1x2 = calcola_edge_pct(m['best_1x2'][1], float(m['best_1x2'][2]))
                                kelly_1x2 = kelly_fraction(m['best_1x2'][1], float(m['best_1x2'][2]))
                                edge_color = "#27ae60" if edge_1x2 > 0 else "#e74c3c"
                                st.markdown(
                                    f"<div class='pure-1x2' style='text-align:center;'>"
                                    f"👑 Miglior Segno Secco<br>"
                                    f"<span style='font-size:1.8em; font-weight:900;'>{m['best_1x2'][0]}</span><br>"
                                    f"Prob: {m['best_1x2'][1]:.1f}% | "
                                    f"<span style='color:{edge_color}; font-weight:bold;'>Edge: {edge_1x2:+.1f}%</span><br>"
                                    f"<span class='{bc}' style='margin-top:5px; display:inline-block;'>"
                                    f"Q {bl}: {m['best_1x2'][2]}</span> "
                                    f"<span class='kelly-tag'>Kelly: {kelly_1x2*100:.1f}%</span>"
                                    f"</div>", unsafe_allow_html=True)

                        with pred_c2:
                            exclude_safe = ["U4.5", "O0.5", "O1.5", "Casa O0.5", "Ospite O0.5"]
                            filtered = {k: v for k, v in m['all_tips'].items()
                                        if k not in exclude_safe}
                            top_3 = sorted(filtered.items(), key=lambda x: x[1], reverse=True)[:3]

                            rows_html = ""
                            medals = ["🥇", "🥈", "🥉"]
                            for idx, (tip_k, tip_v) in enumerate(top_3):
                                q_f, _ = get_quota_finale(tip_k, tip_v, m['quote_reali'])
                                edge_f  = calcola_edge_pct(tip_v, q_f)
                                edge_col = "#27ae60" if edge_f > 0 else "#e74c3c"
                                rows_html += (
                                    f"<div style='margin-bottom:8px;'>"
                                    f"{medals[idx]} <b>{tip_k}</b> ({tip_v:.1f}%) "
                                    f"<span class='quota-badge-calc' style='float:right;'>Q: {q_f}</span> "
                                    f"<span style='color:{edge_col}; font-size:0.8em;'>{edge_f:+.1f}%</span>"
                                    f"</div>")

                            st.markdown(
                                f"<div style='background-color:#f8f9fa; padding:15px; border-radius:8px;"
                                f"border:1px solid #e1e4e8; height:100%;'>"
                                f"<div style='font-weight:700; margin-bottom:10px; color:#2c3e50; font-size:1.1em;'>"
                                f"🔝 TOP 3 OMNI-MARKET</div>"
                                f"{rows_html}"
                                f"</div>", unsafe_allow_html=True)

                        st.markdown("---")
                        st.markdown("### 📊 CONFRONTO FORZE IN CAMPO")
                        col_h, col_vs, col_a = st.columns([4, 1, 4])

                        def scheda_squadra(col, nome_s, rank, xg, forma, stan,
                                           count, t1_s, sq, gk_out, def_out,
                                           stile, poss, parate, conv, cs, fts, colore):
                            with col:
                                st.markdown(
                                    f"<div style='border-left:4px solid {colore}; "
                                    f"background-color:#f4f9fd; padding:12px; border-radius:0 8px 8px 0;'>",
                                    unsafe_allow_html=True)
                                rank_lbl = "" if camp in COPPE_EUROPEE else f" (Pos: {rank}ª)"
                                st.markdown(
                                    f"<h4 style='margin-top:0; color:{colore};'>"
                                    f"{'🏠' if colore == '#2980b9' else '✈️'} {nome_s}{rank_lbl}</h4>",
                                    unsafe_allow_html=True)
                                st.markdown(
                                    f"<div style='font-size:1.8em; font-weight:900; color:{colore}; "
                                    f"margin-bottom:10px;'>xG: {xg:.2f}</div>",
                                    unsafe_allow_html=True)
                                st.write(f"**Forma:** <span class='form-box'>{forma}</span> ({stan})",
                                         unsafe_allow_html=True)
                                star_b  = f" (<span class='star-testo'>{t1_s} Star</span>)" if t1_s > 0 else ""
                                sq_b    = f" <span class='star-testo'>[{sq} 🟥]</span>" if sq > 0 else ""
                                gk_b    = " 🧤🚫" if gk_out else ""
                                def_b   = " 🧱⚠️" if def_out >= 2 else ""
                                st.write(f"**Assenti:** 🚑 {count}{star_b}{sq_b}{gk_b}{def_b}",
                                         unsafe_allow_html=True)
                                st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
                                st.write(f"**Stile:** {stile}")
                                st.write(f"Possesso: **{poss:.1f}%** | Parate: **{parate:.1f}**")
                                st.write(f"Cinismo: **1 gol ogni {conv:.1f} tiri**")
                                st.write(
                                    f"Difesa: CS <span class='cs-testo'>{cs:.0f}%</span> | "
                                    f"A secco <span class='fts-testo'>{fts:.0f}%</span>",
                                    unsafe_allow_html=True)
                                st.markdown("</div>", unsafe_allow_html=True)

                        scheda_squadra(col_h, m['c_s'], m['rank_c'], m['xg_c'],
                                       m['forma_c'], m['stan_c'],
                                       m['count_c'], m['t1_c'], m['sq_c'],
                                       m['gk_out_c'], m['def_out_c'],
                                       m['stile_c'], m['poss_c'], m['parate_c'],
                                       m['conv_c'], m['cs_c'], m['fts_c'], "#2980b9")

                        with col_vs:
                            st.markdown(
                                "<div style='text-align:center; height:100%; display:flex; "
                                "align-items:center; justify-content:center;'>"
                                "<h3 style='color:#bdc3c7;'>VS</h3></div>",
                                unsafe_allow_html=True)

                        scheda_squadra(col_a, m['t_s'], m['rank_t'], m['xg_t'],
                                       m['forma_t'], m['stan_t'],
                                       m['count_t'], m['t1_t'], m['sq_t'],
                                       m['gk_out_t'], m['def_out_t'],
                                       m['stile_t'], m['poss_t'], m['parate_t'],
                                       m['conv_t'], m['cs_t'], m['fts_t'], "#e74c3c")

                        st.markdown("---")
                        b1, b2 = st.columns([1, 1.5])
                        with b1:
                            st.markdown(
                                "<p style='font-size:0.9em; font-weight:bold; color:#7f8c8d; "
                                "margin-bottom:5px; text-transform:uppercase;'>Metriche Gara</p>",
                                unsafe_allow_html=True)
                            st.markdown(f"🚩 **Corner Previsti:** {m['corn_tot']:.1f}")
                            st.markdown(f"🟨 **Cartellini Previsti:** {m['cart_tot']:.1f}")
                            st.markdown(f"🛑 **Falli Totali:** {m['falli_tot']:.1f}")
                        with b2:
                            st.markdown(
                                "<p style='font-size:0.9em; font-weight:bold; color:#7f8c8d; "
                                "margin-bottom:5px; text-transform:uppercase;'>Ritardi & Storico</p>",
                                unsafe_allow_html=True)
                            st.markdown(
                                f"**Ritardi Casa:** <span class='ritardo-testo'>{m['rit_c']}</span>",
                                unsafe_allow_html=True)
                            st.markdown(
                                f"**Ritardi Ospite:** <span class='ritardo-testo'>{m['rit_t']}</span>",
                                unsafe_allow_html=True)
                            st.markdown(
                                f"**DNA Storico:** <span class='dna-testo'>{m['dna_h2h']}</span>",
                                unsafe_allow_html=True)
                            with st.expander("🔍 Dettaglio Scontri Diretti", expanded=False):
                                st.markdown(
                                    f"<div style='font-size:0.85em; background:#f4f6f7; "
                                    f"padding:10px; border-radius:5px;'>{m['dettagli_h2h']}</div>",
                                    unsafe_allow_html=True)

    # ─── TAB 3: Schedine Automatiche ────────────────────────────────────────────
    with t3:
        st.header("🏆 Generatore Automatico Ottimizzato V90")
        st.info(
            "**Novità V90 Fixed**: Le schedine sono ora ordinate per **Value Bet (Edge%)**. "
            "Le puntate seguono il **Kelly Criterion** (25% frazionato) invece dell'allocazione "
            "fissa 60/30/10 — ogni scommessa riceve un budget proporzionale al suo edge reale.")

        if len(st.session_state.all_tips_global) >= 4:
            testo_export = f"=== MATRIX V90 FIXED: SCHEDINE ===\nPeriodo: {start_str} / {end_str}\n\n"

            def mostra_schedina(titolo: str, classe_css: str, pool_filtrato: list,
                                 min_q: float, max_q: float, target: float,
                                 max_q_match: float, escludi: set, budget: float,
                                 note: str = ""):
                st.markdown(f"<div class='strategy-box {classe_css}'>", unsafe_allow_html=True)
                st.subheader(titolo)
                if note:
                    st.caption(note)
                st.markdown(
                    f"<span class='budget-tag'>💰 Budget allocato: {budget:.2f}€</span>",
                    unsafe_allow_html=True)

                slip, q_tot, prob, usate = costruisci_schedina_dinamica(
                    pool_filtrato, min_q, max_q, target,
                    escludi_match=escludi, max_match_q=max_q_match)

                txt = f"{titolo} (Budget: {budget:.2f}€)\n"
                for x in slip:
                    bc    = "quota-badge" if x['Real'] else "quota-badge-calc"
                    edge  = x.get('Edge', 0)
                    kelly_pct = x.get('Kelly', 0) * 100
                    # Puntata suggerita da Kelly su questo budget
                    puntata_k = budget * x.get('Kelly', 0)
                    edge_col  = "#27ae60" if edge > 0 else "#e74c3c"
                    st.write(
                        f"• <span class='orario-match'>[{x['Time']}]</span> "
                        f"{x['Match']}: **{x['Tip']}** "
                        f"<span class='{bc}'>Q: {x['Quota']}</span> "
                        f"<span style='color:{edge_col}; font-size:0.85em;'>Edge: {edge:+.1f}%</span> "
                        f"<span class='kelly-tag'>Kelly: {kelly_pct:.1f}% → {puntata_k:.2f}€</span>",
                        unsafe_allow_html=True)
                    txt += (f"  [{x['Time']}] {x['Match']} -> {x['Tip']} "
                            f"@ {x['Quota']:.2f} | Edge: {edge:+.1f}% | "
                            f"Kelly: {kelly_pct:.1f}% ({puntata_k:.2f}€)\n")

                c1, c2 = st.columns(2)
                c1.metric("Vincita Stimata",         f"~{budget * q_tot:.2f}€")
                c2.metric("Probabilità Congiunta",   f"{prob*100:.2f}%")
                txt += (f"Quota Totale: {q_tot:.2f} | "
                        f"Prob: {prob*100:.2f}% | "
                        f"Vincita: ~{budget * q_tot:.2f}€\n\n")
                st.markdown("</div>", unsafe_allow_html=True)
                return usate, txt

            # Budget: allocazione dinamica Kelly aggregata
            # Invece del 60/30/10 fisso, calcoliamo la Kelly media per categoria
            kelly_pool    = st.session_state.all_tips_global
            kelly_safety  = [x for x in kelly_pool if 1.12 <= float(x['Quota']) <= 1.50]
            kelly_perf    = [x for x in kelly_pool if 1.51 <= float(x['Quota']) <= 2.20]
            kelly_azzardo = [x for x in kelly_pool if 2.21 <= float(x['Quota']) <= 4.50]

            avg_kelly_s = sum(x['Kelly'] for x in kelly_safety[:6])  / max(1, len(kelly_safety[:6]))
            avg_kelly_p = sum(x['Kelly'] for x in kelly_perf[:6])    / max(1, len(kelly_perf[:6]))
            avg_kelly_a = sum(x['Kelly'] for x in kelly_azzardo[:6]) / max(1, len(kelly_azzardo[:6]))

            tot_kelly    = avg_kelly_s + avg_kelly_p + avg_kelly_a
            if tot_kelly == 0: tot_kelly = 1.0

            budget_safety  = budget_totale * (avg_kelly_s / tot_kelly)
            budget_perf    = budget_totale * (avg_kelly_p / tot_kelly)
            budget_azzardo = budget_totale * (avg_kelly_a / tot_kelly)

            vietati_safety = ["Goal", "O1.5", "O2.5", "O3.5", "O4.5"]
            pool_safety_f  = [x for x in kelly_pool if x['Tip'] not in vietati_safety]

            usate_s, txt_s = mostra_schedina(
                "🟢 Schedina SAFETY (Value-First)",
                "safety-bg", pool_safety_f, 1.12, 1.50, 2.0, 2.0,
                set(), budget_safety,
                "Solo scommesse con edge > 0% e quota 1.12–1.50.")
            testo_export += txt_s

            usate_p, txt_p = mostra_schedina(
                "🟠 Schedina PERFORMANCE",
                "performance-bg", kelly_pool, 1.51, 2.20, 5.0, 2.20,
                usate_s, budget_perf,
                "Quote medie, max un evento per partita, priorità all'edge.")
            testo_export += txt_p

            _, txt_a = mostra_schedina(
                "🔴 Schedina AZZARDO",
                "risk-bg", kelly_pool, 2.21, 4.50, 30.0, 4.50,
                usate_p, budget_azzardo,
                "Quote alte. Solo il 10% del capitale in questa fascia.")
            testo_export += txt_a

            st.download_button(
                label="💾 SCARICA TUTTE LE 3 SCHEDINE (TXT)",
                data=testo_export,
                file_name=f"Matrix_V90_Fixed_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain"
            )
