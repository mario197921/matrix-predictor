import streamlit as st
import requests
import math
import pandas as pd
from datetime import datetime, timezone, timedelta
import pytz

# ==========================================
# 🎨 UI: TOTAL MATRIX DESIGN (V91 QUANTUM)
# ==========================================
st.set_page_config(page_title="Matrix Bet V91", page_icon="🎯", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1a1a1a; }
    .stExpander { border: 1px solid #e1e4e8 !important; background-color: #ffffff !important; border-radius: 10px !important; box-shadow: 0 1px 4px rgba(0,0,0,0.03) !important; margin-bottom: 10px !important; }
    .stMetric { background-color: #fcfcfc; border: 1px solid #eee; padding: 12px; border-radius: 10px; }
    h1, h2, h3, p, span, label { color: #1a1a1a !important; font-family: 'Segoe UI', sans-serif; }
    .label-bold { font-weight: 700; color: #444; font-size: 0.85em; text-transform: uppercase; margin-bottom: 5px; display: block; }
    .strategy-box { padding: 20px; border-radius: 15px; margin-bottom: 20px; border: 2px solid #e1e4e8; }
    .safety-bg { background-color: #f0fff4; border-color: #38a169; border-left: 5px solid #27ae60; }
    .performance-bg { background-color: #fffaf0; border-color: #dd6b20; border-left: 5px solid #d35400;}
    .risk-bg { background-color: #fff5f5; border-color: #e53e3e; border-left: 5px solid #c0392b;}
    .builder-bg { background-color: #f5f0ff; border-color: #805ad5; border-left: 5px solid #8e44ad;}
    .form-box { letter-spacing: 2px; font-family: monospace; font-weight: bold; }
    .ritardo-testo { color: #e53e3e; font-size: 0.85em; font-weight: bold; }
    .dna-testo { color: #8e44ad; font-size: 0.85em; font-weight: bold; }
    .streak-testo, .andata-testo, .mot-testo { font-size: 0.85em; font-weight: bold; padding: 3px 8px; border-radius: 5px; display: inline-block; margin-top: 5px; margin-right: 5px;}
    .streak-testo { color: #e74c3c; background-color: #fceae9; border: 1px solid #fadbd8; }
    .andata-testo { color: #2980b9; background-color: #ebf5fb; border: 1px solid #d6eaf8; }
    .mot-testo { color: #1a1a1a; background-color: #fcf3cf; border: 1px solid #f1c40f; }
    .orario-match { color: #e67e22; font-weight: bold; font-family: monospace; font-size: 1.1em; }
    .quota-badge { background-color: #2ecc71; padding: 3px 8px; border-radius: 4px; font-size: 0.85em; color: #ffffff; margin-left: 5px; font-weight: bold;}
    .quota-badge-calc { background-color: #95a5a6; padding: 3px 8px; border-radius: 4px; font-size: 0.85em; color: #ffffff; margin-left: 5px;}
    .pure-1x2 { margin-top: 15px; margin-bottom: 15px; padding: 10px; background-color: #fdfaf0; border-radius: 8px; border-left: 5px solid #f1c40f; font-size: 1.05em; }
    .star-testo { color: #c0392b; font-weight: bold; font-size: 0.85em; }
    .h2h-details { font-size: 0.75em; color: #555; margin-top: 8px; padding: 8px; background-color: #f8f9fa; border-radius: 5px; border-left: 3px solid #8e44ad; }
    .stats-box { background-color: #f4f6f7; padding: 12px; border-radius: 8px; border-left: 4px solid #3498db; margin-top: 10px; font-size: 0.9em;}
    .stile-orizzontale { color: #2980b9; font-weight: bold; }
    .stile-verticale { color: #c0392b; font-weight: bold; }
    .cs-testo { color: #27ae60; font-weight: bold; }
    .fts-testo { color: #c0392b; font-weight: bold; }
    .budget-tag { font-size: 1.1em; font-weight: bold; color: #2c3e50; margin-bottom: 10px; display: inline-block; padding: 5px 10px; background-color: #ecf0f1; border-radius: 5px; border-left: 4px solid #34495e; }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURAZIONE E CAMPIONATI V91 ---
API_KEY_FOOTBALL = 'dc4d6488653c2d9a763290a44eb1613f'
STAGIONE = "2025" # Manteniamo per retrocompatibilità temporanea col resto del codice
HEADERS = {'x-apisports-key': API_KEY_FOOTBALL}

MASTER_LEAGUES = {
    # --- TOP EUROPEI E COPPE ---
    "🇪🇺 Champions League": 2, "🇪🇺 Europa League": 3, "🇪🇺 Conference League": 848,
    "🇮🇹 Serie A": 135, "🇮🇹 Serie B": 136, "🇮🇹 Serie C - Girone A": 137, "🇮🇹 Serie C - Girone B": 138, "🇮🇹 Serie C - Girone C": 139,
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": 39, "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Championship": 40, "🏴󠁧󠁢󠁥󠁮󠁧󠁿 League One": 41, "🏴󠁧󠁢󠁥󠁮󠁧󠁿 League Two": 42,
    "🇪🇸 La Liga": 140, "🇪🇸 La Liga 2": 141, 
    "🇩🇪 Bundesliga": 78, "🇩🇪 2. Bundesliga": 79, 
    "🇫🇷 Ligue 1": 61,
    
    # --- RESTO D'EUROPA E NORDICHE ---
    "🇳🇱 Eredivisie": 88, "🇳🇱 Eerste Divisie": 89, 
    "🇵🇹 Primeira Liga": 94, "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Prem.": 281,
    "🇹🇷 Süper Lig": 203, "🇧🇪 Pro League": 144, "🇬🇷 Super League": 197,
    "🇸🇪 Allsvenskan": 113, "🇳🇴 Eliteserien": 71, "🇫🇮 Veikkausliiga": 244,
    "🇩🇰 Superliga": 119, "🇨🇭 Super League": 207, "🇦🇹 Bundesliga": 218,

    # --- BALCANI ---
    "🇭🇷 HNL (Croazia)": 210, "🇷🇸 Super Liga (Serbia)": 288, "🇷🇴 Liga I (Romania)": 283,

    # --- AMERICHE E COPPE ---
    "🌎 Copa Libertadores": 13, "🌎 Copa Sudamericana": 11, "🌎 CONCACAF Champions": 16,
    "🇧🇷 Brasileirão": 71, "🇦🇷 Liga Profesional": 128, 
    "🇺🇸 MLS": 253, "🇲🇽 Liga MX": 228, "🇨🇴 Primera A (Colombia)": 239,

    # --- ASIA, OCEANIA E COPPE ---
    "🌏 AFC Champions League (Asia)": 17,
    "🇯🇵 J1 League (Giappone)": 98, "🇰🇷 K League 1 (Corea)": 292,
    "🇦🇺 A-League (Australia)": 188, "🇸🇦 Saudi Pro League": 307
}

# --- DATABASE LOGICO V91 ---
BLACKLIST_UNDER = ["Bayern Munich", "Barcelona", "Galatasaray", "Besiktas"]
# Aggiunti gli ID 13 (Libertadores), 11 (Sudamericana) e 16 (CONCACAF) alle leghe solari
LEAGHE_2026 = [113, 71, 244, 128, 253, 228, 239, 98, 292, 13, 11, 16]
# ==========================================
# 📡 SCUDO ANTI-CRASH E MOTORE ESTRAZIONE
# ==========================================
def get_season(league_id):
    """Assegna l'anno solare dinamico."""
    return "2026" if int(league_id) in LEAGHE_2026 else "2025"

def fetch_api_data(endpoint, params):
    """Scudo universale per non far esplodere la pagina se l'API salta o mancano dati."""
    url = f"https://v3.football.api-sports.io/{endpoint}"
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if "errors" in data and data["errors"]: return []
        return data.get("response", [])
    except Exception as e:
        return []

@st.cache_data(ttl=3600)
def get_active_leagues(start_date, end_date):
    active_ids = set()
    delta = end_date - start_date
    days = min(delta.days + 1, 7) 
    now_utc = datetime.now(timezone.utc)
    
    try:
        for i in range(days):
            d_str = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
            resp = fetch_api_data("fixtures", {'date': d_str})
            if resp: 
                for f in resp:
                    # 1. Ignoriamo partite posticipate, cancellate o sospese
                    if f['fixture']['status']['short'] in ['PST', 'CANC', 'ABD', 'AWD', 'WO']:
                        continue
                    
                    # 2. Ignoriamo le partite che sono GIÀ INIZIATE o FINITE oggi
                    try:
                        match_time_utc = datetime.fromisoformat(f['fixture']['date'])
                        if match_time_utc <= now_utc:
                            continue
                    except:
                        pass
                        
                    active_ids.add(f['league']['id'])
                    
        return {k: v for k, v in MASTER_LEAGUES.items() if v in active_ids}
    except: return MASTER_LEAGUES

@st.cache_data(ttl=86400)
def get_player_advanced_stats(player_id, season):
    if not player_id: return "Unknown", 0, 0, 6.0, 0
    resp = fetch_api_data("players", {'id': player_id, 'season': season})
    if resp:
        try:
            stats = resp[0]['statistics'][0]
            pos = stats['games']['position']
            mins = stats['games']['minutes'] or 0
            rating = float(stats['games']['rating'] or 6.0)
            goals = stats['goals']['total'] or 0
            assists = stats['goals']['assists'] or 0
            return pos, goals, assists, rating, mins
        except: pass
    return "Unknown", 0, 0, 6.0, 0

@st.cache_data(ttl=3600)
def calcola_impatto_infortuni(fixture_id, id_casa, id_trasf):
    data = fetch_api_data("injuries", {"fixture": fixture_id})
    if not data: return 0, 0, 1.0, 1.0, "Rosa Completa ✅", "Rosa Completa ✅"

    assenti_c, assenti_t = 0, 0
    visti = set()  # IL FILTRO ANTI-DOPPIONI

    for p in data:
        p_id = p.get('player', {}).get('id')
        # Se l'ID è vuoto o lo abbiamo già contato, lo saltiamo
        if not p_id or p_id in visti: continue
        visti.add(p_id)

        if p['team']['id'] == id_casa: 
            assenti_c += 1
        elif p['team']['id'] == id_trasf: 
            assenti_t += 1

    def get_malus_and_msg(num):
        if num == 0: return 1.0, "Rosa Completa ✅"
        elif num <= 2: return 1.0, f"🚑 {num} Assenti (Lieve)"
        elif num <= 4: return 0.90, f"🚑 {num} Assenti (Pesante -10%)"
        else: return 0.75, f"🚑 {num} Assenti (EMERGENZA -25% ⚠️)"

    malus_c, msg_c = get_malus_and_msg(assenti_c)
    malus_t, msg_t = get_malus_and_msg(assenti_t)

    return assenti_c, assenti_t, malus_c, malus_t, msg_c, msg_t

@st.cache_data(ttl=3600)
def scarica_quote_native(league_id, date_str):
    resp = fetch_api_data("odds", {'league': league_id, 'season': get_season(league_id), 'date': date_str, 'bookmaker': 8})
    quote_dict = {}
    for item in resp:
        fix_id = item['fixture']['id']
        quote_dict[fix_id] = {}
        if item['bookmakers']:
            for bet in item['bookmakers'][0]['bets']:
                if bet['id'] == 1:
                    for val in bet['values']:
                        if val['value'] == 'Home': quote_dict[fix_id]['1'] = float(val['odd'])
                        elif val['value'] == 'Draw': quote_dict[fix_id]['X'] = float(val['odd'])
                        elif val['value'] == 'Away': quote_dict[fix_id]['2'] = float(val['odd'])
                elif bet['id'] == 5:
                    for val in bet['values']:
                        if "Over" in val['value']: quote_dict[fix_id][f"O{val['value'].split(' ')[1]}"] = float(val['odd'])
                        elif "Under" in val['value']: quote_dict[fix_id][f"U{val['value'].split(' ')[1]}"] = float(val['odd'])
                elif bet['id'] == 12:
                    for val in bet['values']:
                        if val['value'] == 'Home/Draw': quote_dict[fix_id]['1X'] = float(val['odd'])
                        elif val['value'] == 'Draw/Away': quote_dict[fix_id]['X2'] = float(val['odd'])
                        elif val['value'] == 'Home/Away': quote_dict[fix_id]['12'] = float(val['odd'])
                elif bet['id'] == 6:
                    for val in bet['values']:
                        if val['value'] == 'Yes': quote_dict[fix_id]['Goal'] = float(val['odd'])
                        elif val['value'] == 'No': quote_dict[fix_id]['NoGoal'] = float(val['odd'])
    return quote_dict

@st.cache_data(ttl=86400)
def analizza_statistiche_stagionali(league_id, team_id):
    resp = fetch_api_data("teams/statistics", {'league': league_id, 'season': get_season(league_id), 'team': team_id})
    if not resp: return 0.0, 0.0
    stats = resp
    giocate = stats.get('fixtures', {}).get('played', {}).get('total', 0)
    if giocate == 0: return 0.0, 0.0
    cs_tot = stats.get('clean_sheet', {}).get('total', 0)
    fts_tot = stats.get('failed_to_score', {}).get('total', 0)
    return (cs_tot / giocate) * 100, (fts_tot / giocate) * 100

@st.cache_data(ttl=3600)
def analizza_statistiche_avanzate_pro(team_id):
    matches = fetch_api_data("fixtures", {'team': team_id, 'last': 10, 'status': 'FT'})
    if not matches: return 50.0, 4.0, 5.0, 5.0, 4.5, 2.0, 10.0, 2.5, "Bilanciato"
    
    tot_poss, tot_tiri, tot_tiri_area, tot_gol, tot_corner = 0, 0, 0, 0, 0
    tot_cart, tot_falli, tot_parate = 0, 0, 0
    match_v = 0
    
    for m in matches:
        fix_id = m['fixture']['id']
        stats_resp = fetch_api_data("fixtures/statistics", {'fixture': fix_id})
        if stats_resp:
            for t_stats in stats_resp:
                if str(t_stats['team']['id']) == str(team_id):
                    s_dict = {s['type']: s['value'] for s in t_stats['statistics']}
                    poss = str(s_dict.get('Ball Possession', '50%')).replace('%', '')
                    tot_poss += int(poss) if poss.isdigit() else 50
                    tot_tiri += int(s_dict.get('Shots on Goal', 0) or 0)
                    tot_tiri_area += int(s_dict.get('Shots insidebox', 0) or 0)
                    tot_corner += int(s_dict.get('Corner Kicks', 0) or 0)
                    tot_falli += int(s_dict.get('Fouls', 0) or 0)
                    tot_parate += int(s_dict.get('Goalkeeper Saves', 0) or 0)
                    tot_cart += int(s_dict.get('Yellow Cards', 0) or 0) + int(s_dict.get('Red Cards', 0) or 0)
                    
                    is_home = str(m['teams']['home']['id']) == str(team_id)
                    tot_gol += int(m['goals']['home'] if is_home else m['goals']['away'])
                    match_v += 1
                    
    if match_v == 0: match_v = 1 
    
    avg_poss = tot_poss / match_v
    avg_tiri_area = tot_tiri_area / match_v
    tiri_per_gol = (tot_tiri / tot_gol) if tot_gol > 0 else 10.0 
    
    if avg_poss > 55 and avg_tiri_area < 4: stile = "Tiki-Taka Sterile"
    elif avg_poss < 45 and avg_tiri_area > 4: stile = "Verticale Diretto"
    else: stile = "Bilanciato"
    
    return avg_poss, tot_tiri / match_v, avg_tiri_area, tiri_per_gol, tot_corner / match_v, tot_cart / match_v, tot_falli / match_v, tot_parate / match_v, stile

def get_quota_finale(tip, prob, quote_reali):
    if quote_reali and tip in quote_reali: return quote_reali[tip], True
    if prob <= 0: return 50.0, False
    
    # Nessun trucco: probabilità reale al 100% con aggio del bookmaker al 6%
    quota_fair = 100.0 / prob
    quota_mercato = quota_fair * 0.94
        
    return round(min(30.0, max(1.01, quota_mercato)), 2), False

@st.cache_data(ttl=3600)
def analizza_squadra_globale(team_id):
    matches = fetch_api_data("fixtures", {'team': team_id, 'last': 10, 'status': 'FT'})
    if not matches: return 1.0, False, "N/D", 1.0, "Nessuno"
    
    ultima_data = datetime.strptime(matches[0]['fixture']['date'][:10], '%Y-%m-%d')
    diff_giorni = (datetime.now() - ultima_data).days
    is_stanca = diff_giorni <= 4
    
    forma_str, punti = "", 0
    for m in matches[:5]:
        is_home = str(m['teams']['home']['id']) == str(team_id)
        gh, ga = m['goals']['home'], m['goals']['away']
        if gh == ga: forma_str += "D"; punti += 1
        elif (is_home and gh > ga) or (not is_home and ga > gh): forma_str += "W"; punti += 3
        else: forma_str += "L"
    forma_str = forma_str[::-1] 
    
    stats = {'W': 0, 'D': 0, 'L': 0, 'Over': 0, 'Goal': 0}
    for m in matches:
        is_home = str(m['teams']['home']['id']) == str(team_id)
        gh, ga = m['goals']['home'], m['goals']['away']
        if gh is not None and ga is not None:
            if gh == ga: stats['D'] += 1
            elif (is_home and gh > ga) or (not is_home and ga > gh): stats['W'] += 1
            else: stats['L'] += 1
            if (gh + ga) > 2: stats['Over'] += 1
            if gh > 0 and ga > 0: stats['Goal'] += 1
            
    ritardi = []
    if stats['D'] == 0: ritardi.append("X")
    if stats['W'] == 0: ritardi.append("Vittoria")
    if stats['Over'] == 0: ritardi.append("Over 2.5")
    if stats['Goal'] == 0: ritardi.append("Goal")

    return 0.95 if is_stanca else 1.0, is_stanca, forma_str, 0.9 + ((punti/15)*0.2), (", ".join(ritardi) if ritardi else "Nessuno")

@st.cache_data(ttl=3600)
def analizza_h2h_dna_e_andata(id_casa, id_trasf):
    matches = fetch_api_data("fixtures/headtohead", {'h2h': f"{id_casa}-{id_trasf}", 'last': 5})
    if not matches: return 1.0, 1.0, 0, 0, "Nessun Precedente", 1.0, 1.0, "", "Nessun match."
    
    vittorie_c, vittorie_t, gol_c, gol_t = 0, 0, 0, 0
    andata_msg, boost_andata_c, boost_andata_t = "", 1.0, 1.0
    dettagli_list = []
    
    for m in matches:
        if m['goals']['home'] is not None:
            d_m = datetime.strptime(m['fixture']['date'][:10], '%Y-%m-%d').strftime('%d/%m/%Y')
            dettagli_list.append(f"📅 {d_m}: {m['teams']['home']['name']} <b>{m['goals']['home']} - {m['goals']['away']}</b> {m['teams']['away']['name']}")
            
            is_home_now = m['teams']['home']['id'] == id_casa
            gc, gt = (m['goals']['home'], m['goals']['away']) if is_home_now else (m['goals']['away'], m['goals']['home'])
            gol_c += gc; gol_t += gt
            if gc > gt: vittorie_c += 1
            elif gt > gc: vittorie_t += 1

    dettagli_str = "<br>".join(dettagli_list) if dettagli_list else "Nessun match."
    
    ultimo_match = matches[0]
    data_ultimo = datetime.strptime(ultimo_match['fixture']['date'][:10], '%Y-%m-%d')
    
    # FIX V91: Controlliamo se l'ultimo match era di una coppa/torneo eliminatorio leggendo il nome della lega
    nome_lega = str(ultimo_match.get('league', {}).get('name', '')).lower()
    is_coppa_h2h = any(x in nome_lega for x in ['cup', 'coppa', 'copa', 'champions', 'europa', 'conference', 'libertadores'])

    # Si attiva l'effetto Andata/Ritorno SOLO se è una coppa E giocata da meno di 28 giorni
    if is_coppa_h2h and (datetime.now() - data_ultimo).days <= 28:
        is_home_last = ultimo_match['teams']['home']['id'] == id_casa
        gc_last, gt_last = ultimo_match['goals']['home'], ultimo_match['goals']['away']
        if gc_last is not None and gt_last is not None:
            g_c_and = gc_last if is_home_last else gt_last
            g_t_and = gt_last if is_home_last else gc_last
            diff = g_c_and - g_t_and
            andata_msg = f"🏆 Andata: {g_c_and} - {g_t_and}"
            if diff in [-1, -2]: boost_andata_c = 1.25; andata_msg += " (Casa all'assalto ⚔️)"
            elif diff in [1, 2]: boost_andata_t = 1.25; andata_msg += " (Ospiti all'assalto ⚔️)"
            elif diff <= -3 or diff >= 3: boost_andata_c = 0.85; boost_andata_t = 0.85; andata_msg += " (Qualificazione chiusa 🛡️)"
    
    m_count = max(1, len([m for m in matches if m['goals']['home'] is not None]))
    m_h2h_c = min(1.20, max(0.80, 0.90 + (vittorie_c/m_count)*0.20 + (gol_c/(m_count*max(1, gol_c+gol_t)))*0.10))
    m_h2h_t = min(1.20, max(0.80, 0.90 + (vittorie_t/m_count)*0.20 + (gol_t/(m_count*max(1, gol_c+gol_t)))*0.10))
    
    storico_str = f"Vittorie: 🏠 {vittorie_c} - {vittorie_t} ✈️ | Gol H2H: {gol_c} a {gol_t}"
    return m_h2h_c, m_h2h_t, gol_c, gol_t, storico_str, boost_andata_c, boost_andata_t, andata_msg, dettagli_str

@st.cache_data(ttl=3600)
def scarica_meteo(citta):
    try:
        url = f"https://wttr.in/{citta}?format=j1"
        resp = requests.get(url, timeout=3).json()
        cond = resp['current_condition'][0]['weatherDesc'][0]['value']
        pioggia = any(p in cond.lower() for p in ['rain', 'snow', 'shower', 'thunder'])
        return (0.90, f"🌧️ {cond}") if pioggia else (1.0, f"☀️ {cond}")
    except: return 1.0, "🌥️ Dato N/D"

# ==========================================
# 🧮 MOTORE MATEMATICO E GENERAZIONE QUOTE
# ==========================================
def calcola_prob_poisson(xg, gol): 
    return ((xg ** gol) * math.exp(-xg)) / math.factorial(gol)

def semplifica_nome(nome):
    for p in ['FC', 'AC ', ' BC', ' AS', ' Milan', ' Calcio', ' Hotspur', 'AFC ', 'United', 'City', 'SL ']: nome = nome.replace(p, '')
    return nome.strip()

def calcola_tutti_i_mercati(xg_c, xg_t, avg_corner_match, avg_cart_match, is_sev, tot_falli_match):
    p = {"1":0,"X":0,"2":0,"1X":0,"X2":0,"12":0,"Goal":0,"NoGoal":0, "Pari":0, "Dispari":0}
    
    # V91.1: Rimossi i Multigol ingiocabili (1-5 e 3-5)
    mg = {"MG 1-3":0, "MG 1-4":0, "MG 2-3":0, "MG 2-4":0, "MG 2-5":0, "MG 3-4":0}
    uo_lines = [1.5, 2.5, 3.5, 4.5, 5.5]
    
    for line in uo_lines: p[f"U{line}"] = 0; p[f"O{line}"] = 0
    p["Casa O0.5"] = 0; p["Ospite O0.5"] = 0

    re_prob = {}
    for gc in range(8):
        for gt in range(8):
            prob = (calcola_prob_poisson(xg_c, gc) * calcola_prob_poisson(xg_t, gt)) * 100
            tot = gc + gt
            if gc > gt: p["1"] += prob
            elif gc == gt: p["X"] += prob
            else: p["2"] += prob
            if gc > 0 and gt > 0: p["Goal"] += prob
            else: p["NoGoal"] += prob
            if tot % 2 == 0: p["Pari"] += prob
            else: p["Dispari"] += prob
            for line in uo_lines:
                if tot < line: p[f"U{line}"] += prob
                else: p[f"O{line}"] += prob
            if gc > 0: p["Casa O0.5"] += prob
            if gt > 0: p["Ospite O0.5"] += prob
            
            if 1 <= tot <= 3: mg["MG 1-3"] += prob
            if 1 <= tot <= 4: mg["MG 1-4"] += prob
            if 2 <= tot <= 3: mg["MG 2-3"] += prob
            if 2 <= tot <= 4: mg["MG 2-4"] += prob
            if 2 <= tot <= 5: mg["MG 2-5"] += prob
            if 3 <= tot <= 4: mg["MG 3-4"] += prob
            
            # Salvataggio Universale dei Risultati Esatti per calcolare le Combo
            re_prob[f"Risultato {gc}-{gt}"] = prob

    p["1X"], p["X2"], p["12"] = (p["1"]+p["X"]), (p["X"]+p["2"]), (p["1"]+p["2"])

    if xg_c > 1.2 and xg_t > 1.2:
        p["Goal"] = min(90.0, p["Goal"] * 1.18) 
        p["NoGoal"] = 100 - p["Goal"]
    elif xg_c < 0.9 and xg_t < 0.9:
        p["NoGoal"] = min(90.0, p["NoGoal"] * 1.15)
        p["Goal"] = 100 - p["NoGoal"]

    # V91.1: CALCOLO ESATTO COMBINATO (Niente più moltiplicatori artificiali)
    combos = {
        "1X + Under 3.5": sum(re_prob.get(f"Risultato {c}-{t}", 0) for c in range(4) for t in range(4) if c >= t and c+t < 3.5),
        "1X + Under 4.5": sum(re_prob.get(f"Risultato {c}-{t}", 0) for c in range(5) for t in range(5) if c >= t and c+t < 4.5),
        "X2 + Under 3.5": sum(re_prob.get(f"Risultato {c}-{t}", 0) for c in range(4) for t in range(4) if t >= c and c+t < 3.5),
        "X2 + Under 4.5": sum(re_prob.get(f"Risultato {c}-{t}", 0) for c in range(5) for t in range(5) if t >= c and c+t < 4.5),
        "1 + Over 1.5": sum(re_prob.get(f"Risultato {c}-{t}", 0) for c in range(8) for t in range(8) if c > t and c+t > 1.5),
        "2 + Over 1.5": sum(re_prob.get(f"Risultato {c}-{t}", 0) for c in range(8) for t in range(8) if t > c and c+t > 1.5),
        "1 + Over 2.5": sum(re_prob.get(f"Risultato {c}-{t}", 0) for c in range(8) for t in range(8) if c > t and c+t > 2.5),
        "2 + Over 2.5": sum(re_prob.get(f"Risultato {c}-{t}", 0) for c in range(8) for t in range(8) if t > c and c+t > 2.5),
        "Goal + Over 2.5": sum(re_prob.get(f"Risultato {c}-{t}", 0) for c in range(8) for t in range(8) if c > 0 and t > 0 and c+t > 2.5),
        "1X + Goal": sum(re_prob.get(f"Risultato {c}-{t}", 0) for c in range(8) for t in range(8) if c >= t and c > 0 and t > 0),
        "X2 + Goal": sum(re_prob.get(f"Risultato {c}-{t}", 0) for c in range(8) for t in range(8) if t >= c and c > 0 and t > 0)
    }

    ht_prob = {"1": p["1"]*0.9, "X": p["X"]*1.5, "2": p["2"]*0.9} 
    tot_ht = sum(ht_prob.values()); ht_prob = {k: v/tot_ht for k,v in ht_prob.items()}
    htft = {}
    for ht in ["1", "X", "2"]:
        for ft in ["1", "X", "2"]: htft[f"HT/FT {ht}/{ft}"] = (ht_prob[ht] * p[ft]) 

    prob_corner_85 = min(92.0, max(15.0, (avg_corner_match / 9.5) * 55))
    tension = avg_cart_match + (1.5 if is_sev else 0) + (tot_falli_match / 20.0) 
    prob_cart_45 = min(88.0, max(20.0, (tension / 5.0) * 55))
    special = {"Over 8.5 Angoli": prob_corner_85, "Over 4.5 Cartellini": prob_cart_45}

    # Pulizia visiva per l'interfaccia (nascondiamo le prob. dei risultati esatti < 5%)
    re_prob_clean = {k: v for k, v in re_prob.items() if v >= 5.0}

    return {**p, **mg, **re_prob_clean, **combos, **htft, **special}

def get_family(tip):
    if tip in ["1", "X", "2", "1X", "X2", "12"]: return "1X2"
    if ("U" in tip or "O" in tip) and "+" not in tip and "Casa" not in tip and "Ospite" not in tip and "Angoli" not in tip and "Cartellini" not in tip: return "UO"
    if "MG" in tip: return "MG"
    if "Goal" in tip or "NoGoal" in tip: return "GGNG"
    if "+" in tip: return "COMBO"
    if "Risultato" in tip: return "RE"
    if "HT/FT" in tip: return "HTFT"
    if tip in ["Pari", "Dispari"]: return "PD"
    if "Angoli" in tip or "Cartellini" in tip: return "SPECIAL"
    return "ALTRO"

# ==========================================
# 💰 MOTORE SCHEDINE E CASSAFORTE (V91)
# ==========================================
def costruisci_schedina_dinamica(pool, min_q, max_q, target_mult, escludi_match=None, max_match_q=5.0, max_righe=12, max_same_family=2, check_blacklist=False, is_cassaforte=False):
    if escludi_match is None: escludi_match = set()
    valid = []
    
    for x in pool:
        q = float(x['Quota'])
        if min_q <= q <= max_q and q <= max_match_q:
            # V91: Blacklist Under per la Safety
            if check_blacklist and "U" in x['Tip'] and "+" not in x['Tip']:
                if any(b_team in x['Match'] for b_team in BLACKLIST_UNDER):
                    continue # Salta e non consigliare Under per questa Big
            
            # V91: La Cassaforte gioca solo mercati super stabili
            if is_cassaforte and get_family(x['Tip']) not in ["UO", "MG", "1X2", "GGNG"]:
                continue

            valid.append(x)
            
    # Ordinamento chirurgico per valore assoluto
    pool_ordinata = sorted(valid, key=lambda x: (x['Prob']/100) * float(x['Quota']), reverse=True)
    
    selezionate, viste_locali, family_counts = [], set(), {}
    q_tot, prob_tot = 1.0, 1.0
    
    for item in pool_ordinata:
        famiglia = get_family(item['Tip'])
        match_name = item['Match']
        
        if match_name not in viste_locali and match_name not in escludi_match and family_counts.get(famiglia, 0) < max_same_family:
            selezionate.append(item)
            viste_locali.add(match_name)
            family_counts[famiglia] = family_counts.get(famiglia, 0) + 1
            q_tot *= float(item['Quota'])
            prob_tot *= (item['Prob'] / 100)
            
        if q_tot >= target_mult or len(selezionate) >= max_righe: break
        
    return selezionate, q_tot, prob_tot, viste_locali.union(escludi_match)

# ==========================================
# 🏠 LOGICA DI STATO E INTERFACCIA V91
# ==========================================
if 'data_master' not in st.session_state: st.session_state.data_master = {}
if 'all_tips_global' not in st.session_state: st.session_state.all_tips_global = []

st.sidebar.header("⚙️ Centrale Operativa V91")

date_range = st.sidebar.date_input("Seleziona Periodo (Dal - Al):", [])
if len(date_range) == 2: start_date, end_date = date_range[0], date_range[1]
elif len(date_range) == 1: start_date = end_date = date_range[0]
else: start_date = end_date = datetime.now().date()

start_str = start_date.strftime('%Y-%m-%d')
end_str = end_date.strftime('%Y-%m-%d')

st.sidebar.markdown("---")
budget_totale = st.sidebar.number_input("💰 Budget Totale Giornaliero (€):", min_value=5.0, value=50.0, step=5.0)
st.sidebar.markdown("---")

with st.sidebar:
    if st.button("🔍 Trova Campionati Attivi"):
        with st.spinner("Scansione palinsesto in corso..."):
            st.session_state['active_leagues'] = get_active_leagues(start_date, end_date)

if 'active_leagues' not in st.session_state: st.session_state['active_leagues'] = MASTER_LEAGUES 
active_dict = st.session_state['active_leagues']
if not active_dict: st.sidebar.warning("Nessun campionato supportato attivo.")
scelte = st.sidebar.multiselect("Campionati in campo:", list(active_dict.keys()), default=list(active_dict.keys()))

btn_genera = st.sidebar.button("⚡ ESTRAI MATRIX V91")

if btn_genera:
    st.session_state.data_master = {}
    st.session_state.all_tips_global = []
    now_utc = datetime.now(timezone.utc)
    tz_ita = pytz.timezone('Europe/Rome')
    mese_attuale = datetime.now().month

    for name in scelte:
        f_id = active_dict[name]
        stagione_dinamica = get_season(f_id)
        
        with st.spinner(f"Analisi V91 (Scudo Anti-Crash) {name}..."):
            fix = fetch_api_data("fixtures", {'league': f_id, 'season': stagione_dinamica, 'from': start_str, 'to': end_str})
            std = fetch_api_data("standings", {'league': f_id, 'season': stagione_dinamica})
            
            if not fix: continue

            db_stats = {}
            punti_champions, punti_salvezza, tot_squadre, partite_totali_campionato = 0, 0, 20, 38
            if std and len(std) > 0 and 'league' in std[0] and 'standings' in std[0]['league']:
                gruppo = std[0]['league']['standings'][0]
                tot_squadre = len(gruppo)
                partite_totali_campionato = (tot_squadre - 1) * 2
                if tot_squadre >= 18:
                    punti_champions = gruppo[3]['points'] 
                    punti_salvezza = gruppo[tot_squadre - 4]['points'] 
                
                for t in gruppo:
                    n = semplifica_nome(t['team']['name'])
                    db_stats[n] = {
                        'id': t['team']['id'], 'rank': t['rank'], 'giocate': t['all']['played'], 'punti': t['points'],
                        'ac': t['home']['goals']['for'] / max(1, t['home']['played']),
                        'dc': t['home']['goals']['against'] / max(1, t['home']['played']),
                        'at': t['away']['goals']['for'] / max(1, t['away']['played']),
                        'dt': t['away']['goals']['against'] / max(1, t['away']['played'])
                    }

            matches_list = []
            date_giocate = {f['fixture']['date'][:10] for f in fix}
            inj_cache = {}
            odds_cache = {}
            for d_match in date_giocate:
                inj_cache[d_match] = fetch_api_data("injuries", {'league': f_id, 'season': stagione_dinamica, 'date': d_match})
                odds_cache[d_match] = scarica_quote_native(f_id, d_match)

            for f in fix:
                if f['fixture']['status']['short'] in ['PST', 'CANC', 'ABD', 'AWD', 'WO']: continue 

                fix_id = f['fixture']['id']
                match_date_str = f['fixture']['date'][:10]
                match_time_utc = datetime.fromisoformat(f['fixture']['date'])
                if match_time_utc <= now_utc: continue
                match_time_ita = match_time_utc.astimezone(tz_ita)
                orario_ita = match_time_ita.strftime('%d/%m %H:%M')

                c_u, t_u = f['teams']['home']['name'], f['teams']['away']['name']
                c_s, t_s = semplifica_nome(c_u), semplifica_nome(t_u)
                if c_s not in db_stats or t_s not in db_stats: continue
                # V91.3: Filtro intelligente. Applica il blocco solo ai campionati (Serie A, B, ecc.) 
                # ma lascia passare le Coppe (Copa, Champions, ecc.) anche se hanno pochi dati.
               

                quote_reali_match = odds_cache.get(match_date_str, {}).get(fix_id, {})
                inf_all = inj_cache.get(match_date_str, [])

                m_st_c, is_stanca_c, forma_c, m_f_c, rit_c = analizza_squadra_globale(db_stats[c_s]['id'])
                m_st_t, is_stanca_t, forma_t, m_f_t, rit_t = analizza_squadra_globale(db_stats[t_s]['id'])
                
                cs_c, fts_c = analizza_statistiche_stagionali(f_id, db_stats[c_s]['id'])
                cs_t, fts_t = analizza_statistiche_stagionali(f_id, db_stats[t_s]['id'])
                
                m_met, d_met = scarica_meteo(c_s)
                m_h2h_c, m_h2h_t, gol_h2h_c, gol_h2h_t, str_h2h, b_and_c, b_and_t, andata_msg, dettagli_h2h_str = analizza_h2h_dna_e_andata(db_stats[c_s]['id'], db_stats[t_s]['id'])
                
                inf_c_list = [i for i in inf_all if semplifica_nome(i['team']['name']) == c_s]
                inf_t_list = [i for i in inf_all if semplifica_nome(i['team']['name']) == t_s]
                
                count_c, count_t, malus_inf_c, malus_inf_t, msg_inf_c, msg_inf_t = calcola_impatto_infortuni(fix_id, db_stats[c_s]['id'], db_stats[t_s]['id'])
                
                streak_breaker_c = (gol_h2h_c == 0) and (count_t > 0 or is_stanca_t)
                streak_breaker_t = (gol_h2h_t == 0) and (count_c > 0 or is_stanca_c)
                
                poss_c, tiri_c, box_c, conv_c, corn_c, cart_c, falli_c, parate_c, stile_c = analizza_statistiche_avanzate_pro(db_stats[c_s]['id'])
                poss_t, tiri_t, box_t, conv_t, corn_t, cart_t, falli_t, parate_t, stile_t = analizza_statistiche_avanzate_pro(db_stats[t_s]['id'])
                
                is_coppa = name in ["🇪🇺 Champions League", "🇪🇺 Europa League", "🇪🇺 Conference League"]
                m_mot_c, m_mot_t, tension_idx = 1.0, 1.0, 1.0
                msg_mot = ""

                if is_coppa and mese_attuale in [3, 4, 5]:
                    m_mot_c, m_mot_t = 1.25, 1.25 
                    tension_idx += 0.3
                    msg_mot = "🔥 DENTRO O FUORI (Coppa)"
                elif not is_coppa:
                    punti_c, punti_t = db_stats[c_s]['punti'], db_stats[t_s]['punti']
                    rank_c, rank_t = db_stats[c_s]['rank'], db_stats[t_s]['rank']

                    if rank_c <= 6 or (punti_champions - punti_c) <= 7 and (punti_champions - punti_c) > 0:
                        m_mot_c = 1.15; msg_mot += "🏆 C. Vertice "
                    elif rank_c >= tot_squadre - 6:
                        m_mot_c = 1.20; msg_mot += "🆘 C. Disperata "
                        tension_idx += 0.15
                    elif mese_attuale >= 3 and (punti_c - punti_salvezza) > 9 and (punti_champions - punti_c) > 10:
                        m_mot_c = 1.10; msg_mot += "🌴 C. Sgombra "
                    else: m_mot_c = 1.05
                    
                    if rank_t <= 6 or (punti_champions - punti_t) <= 7 and (punti_champions - punti_t) > 0:
                        m_mot_t = 1.15; msg_mot += "🏆 O. Vertice"
                    elif rank_t >= tot_squadre - 6:
                        m_mot_t = 1.20; msg_mot += "🆘 O. Disperata"
                        tension_idx += 0.15
                    elif mese_attuale >= 3 and (punti_t - punti_salvezza) > 9 and (punti_champions - punti_t) > 10:
                        m_mot_t = 1.10; msg_mot += "🌴 O. Sgombra"
                    else: m_mot_t = 1.05

                    if abs(rank_c - rank_t) <= 3: tension_idx += 0.2

                # V91.3: Paracadute matematico. Se i dati sono a zero (inizio coppa), 
                # assegna una media minima di 0.8 per evitare l'errore del 100%.
                ac_safe = max(0.8, db_stats[c_s]['ac'])
                dt_safe = max(0.8, db_stats[t_s]['dt'])
                at_safe = max(0.8, db_stats[t_s]['at'])
                dc_safe = max(0.8, db_stats[c_s]['dc'])

                xg_base_c = math.sqrt(ac_safe * dt_safe) * m_f_c * m_st_c
                xg_base_t = math.sqrt(at_safe * dc_safe) * m_f_t * m_st_t
                
                malus_league = 0.85 if name in ["🇬🇷 Super League", "🇫🇷 Ligue 1", "🇮🇹 Serie B"] else 1.0 
                xg_base_c *= malus_league
                xg_base_t *= malus_league

                if conv_c < 3.0: xg_base_c *= 1.15
                elif conv_c > 7.0: xg_base_c *= 0.85
                if conv_t < 3.0: xg_base_t *= 1.15
                elif conv_t > 7.0: xg_base_t *= 0.85
                
                boost_box_c = min(1.20, 1.0 + (box_c / 15.0) * 0.15)
                boost_box_t = min(1.20, 1.0 + (box_t / 15.0) * 0.15)
                xg_base_c *= boost_box_c
                xg_base_t *= boost_box_t
                
                malus_portiere_c = min(0.25, (parate_c / 6.0) * 0.20)
                malus_portiere_t = min(0.25, (parate_t / 6.0) * 0.20)
                xg_base_c *= (1 - malus_portiere_t)
                xg_base_t *= (1 - malus_portiere_c)
                
                tot_falli_match = falli_c + falli_t
                if tot_falli_match > 28:
                    xg_base_c *= 0.90
                    xg_base_t *= 0.90

                if fts_c > 35.0 or cs_t > 35.0: xg_base_c *= 0.85  
                if fts_t > 35.0 or cs_c > 35.0: xg_base_t *= 0.85
                
                se_sgombra_c = "C. Sgombra" in msg_mot
                se_sgombra_t = "O. Sgombra" in msg_mot
                
               # Calcolo Finale xG (con Malus Medico V91)
                xg_c = (xg_base_c * malus_inf_c) * m_h2h_c * b_and_c * m_mot_c * (1.10 if se_sgombra_t else 1.0)
                xg_t = (xg_base_t * malus_inf_t) * m_h2h_t * b_and_t * m_mot_t * (1.10 if se_sgombra_c else 1.0)
                
                msg_streak = ""
                # V91: Nerf Streak Breaker a 1.15 (prima era 1.45)
                if streak_breaker_c: xg_c = max(1.15, xg_c * 1.15); msg_streak += "🔥 STREAK CASA "
                if streak_breaker_t: xg_t = max(1.15, xg_t * 1.15); msg_streak += "🔥 STREAK OSPITE"
                
                xg_c *= m_met; xg_t *= m_met
                
                arb = f['fixture']['referee'] or "N/D"
                is_sev = any(s in str(arb) for s in ["Orsato", "Maresca", "Taylor", "Oliver", "Lahoz", "Hernandez"])
                xg_c *= (1.05 if is_sev else 1.0); xg_t *= (1.05 if is_sev else 1.0)
                
                avg_corner_match = corn_c + corn_t
                avg_cart_match = cart_c + cart_t

                full_tips = calcola_tutti_i_mercati(xg_c, xg_t, avg_corner_match, avg_cart_match, is_sev, tot_falli_match)
                
                best_1x2_key = max(["1", "X", "2"], key=lambda k: full_tips[k])
                if full_tips[best_1x2_key] < 45.0:
                    best_1x2_key, best_1x2_prob, best_1x2_q, best_1x2_real = "No Segno Fisso", 0.0, "-", False
                else:
                    best_1x2_prob = full_tips[best_1x2_key]
                    best_1x2_q, best_1x2_real = get_quota_finale(best_1x2_key, best_1x2_prob, quote_reali_match)

                for k,v in full_tips.items():
                    q_finale, is_real = get_quota_finale(k, v, quote_reali_match)
                    st.session_state.all_tips_global.append({
                        "Match": f"{c_u} vs {t_u}", "League": name, "Tip": k, 
                        "Prob": v, "Quota": q_finale, "Real": is_real, "Time": orario_ita
                    })

                matches_list.append({
                    "orario": orario_ita, "c_u": c_u, "t_u": t_u, "c_s": c_s, "t_s": t_s, 
                    "rank_c": db_stats[c_s]['rank'], "rank_t": db_stats[t_s]['rank'],
                    "cs_c": cs_c, "fts_c": fts_c, "cs_t": cs_t, "fts_t": fts_t,
                    "all_tips": full_tips, "best_1x2": (best_1x2_key, best_1x2_prob, best_1x2_q, best_1x2_real),
                    "quote_reali": quote_reali_match,
                    "xg_c": xg_c, "xg_t": xg_t, "arb": arb, "is_sev": is_sev,
                    "count_c": count_c, "count_t": count_t, "msg_inf_c": msg_inf_c, "msg_inf_t": msg_inf_t,
                    "meteo": d_met, "dna_h2h": str_h2h, "dettagli_h2h": dettagli_h2h_str, "streak_msg": msg_streak.strip(), "andata_msg": andata_msg, "msg_mot": msg_mot.strip(),
                    "stan_c": "⚠️ Fatigue" if is_stanca_c else "✅ Riposo", "stan_t": "⚠️ Fatigue" if is_stanca_t else "✅ Riposo", 
                    "forma_c": forma_c, "forma_t": forma_t, "rit_c": rit_c, "rit_t": rit_t,
                    "poss_c": poss_c, "tiri_c": tiri_c, "conv_c": conv_c, "stile_c": stile_c,
                    "box_c": box_c, "falli_c": falli_c, "parate_c": parate_c,
                    "poss_t": poss_t, "tiri_t": tiri_t, "conv_t": conv_t, "stile_t": stile_t,
                    "box_t": box_t, "falli_t": falli_t, "parate_t": parate_t,
                    "corn_tot": avg_corner_match, "cart_tot": avg_cart_match, "falli_tot": tot_falli_match
                })
            if matches_list: st.session_state.data_master[name] = matches_list

# --- DISPLAY DELLE 3 TAB (V91) ---
if st.session_state.data_master:
    t1, t2, t3 = st.tabs(["🌍 DASHBOARD GLOBALE", "🏆 SCHEDINE AUTOMATICHE", "🔬 ESPLORATORE SINGOLE"])
    
# ---------------------------------------------------------
    # TAB 1: DASHBOARD GLOBALE & BET BUILDER (Completa V91)
    # ---------------------------------------------------------
    with t1:
        st.header("🌍 Dashboard Globale & Bet Builder")
        st.write("Spunta la casella '🛒' per aggiungere le migliori quote al tuo Carrello (calcolato a fine pagina).")

        def mostra_tabella_interattiva(titolo, filter_func, sort_cols, max_rows=10):
            st.subheader(titolo)
            pool = [x for x in st.session_state.all_tips_global if filter_func(x) and float(x['Quota']) >= 1.15]
            if not pool:
                st.info("Nessun dato disponibile per questa categoria.")
                return []
            
            df = pd.DataFrame(pool).sort_values(by=sort_cols, ascending=[False]*len(sort_cols)).head(max_rows)
            df = df[['Match', 'Tip', 'Prob', 'Quota', 'Time']]
            df.insert(0, "🛒", False) 
            
            edited_df = st.data_editor(
                df,
                column_config={
                    "🛒": st.column_config.CheckboxColumn("Sel", default=False),
                    "Prob": st.column_config.NumberColumn("Prob (%)", format="%.1f%%"),
                    "Quota": st.column_config.NumberColumn("Quota", format="%.2f")
                },
                hide_index=True, use_container_width=True, disabled=['Match', 'Tip', 'Prob', 'Quota', 'Time'],
                key=f"editor_{titolo}"
            )
            return edited_df[edited_df["🛒"] == True].to_dict('records')

        # 1. LA REGINA: TOP 10 ASSOLUTA (A larghezza piena)
        sel_assoluta = mostra_tabella_interattiva("👑 TOP 10 ASSOLUTA (Le Probabilità più alte in assoluto)", lambda x: x['Tip'] not in ["U4.5", "U5.5", "Casa O0.5", "Ospite O0.5"], ["Prob"])
        st.markdown("---")

        # 2. LE CATEGORIE SPECIFICHE (Su due colonne)
        col_dash1, col_dash2 = st.columns(2)
        with col_dash1:
            sel_combo = mostra_tabella_interattiva("🏆 TOP 10 COMBO", lambda x: "+" in x['Tip'], ["Prob"])
            sel_1x2 = mostra_tabella_interattiva("🛡️ TOP 10 DOPPIE CHANCE", lambda x: x['Tip'] in ["1X", "X2", "12"], ["Prob"])
            sel_gg = mostra_tabella_interattiva("🎯 TOP 10 GOAL / NOGOAL", lambda x: x['Tip'] in ["Goal", "NoGoal"], ["Prob"])
        with col_dash2:
            sel_mg = mostra_tabella_interattiva("🎯 TOP 10 MULTIGOL", lambda x: "MG" in x['Tip'], ["Prob", "Quota"])
            sel_uo = mostra_tabella_interattiva("⚽ TOP 10 OVER/UNDER", lambda x: ("O" in x['Tip'] or "U" in x['Tip']) and "+" not in x['Tip'], ["Prob"])
            sel_azzardo = mostra_tabella_interattiva("🧨 TOP 10 AZZARDI (Quote alte > 2.50)", lambda x: float(x['Quota']) >= 2.50, ["Prob"])

        st.markdown("---")
        st.markdown("### 🚨 RADAR ANOMALIE (Value Bet & Mine Vaganti)")
        anomalie_trovate = False
        for camp, matches in st.session_state.data_master.items():
            for m in matches:
                is_mina_vagante = ("Sgombra" in m['msg_mot'] and ("Vertice" in m['msg_mot'] or "Disperata" in m['msg_mot']))
                is_dominio_ospite = (m['xg_t'] > m['xg_c'] * 1.3)
                if (is_mina_vagante or is_dominio_ospite) and float(m['best_1x2'][2] if str(m['best_1x2'][2]).replace('.','').isdigit() else 0) > 2.50:
                    anomalie_trovate = True
                    st.error(f"**⚡ [{m['orario']}] {m['c_s']} vs {m['t_s']}**")
                    st.write(f"↳ **Motivazione Matrix:** xG {m['xg_c']:.2f} a {m['xg_t']:.2f}. {m['msg_mot']}")
                    st.write(f"↳ **Giocata Consigliata:** X2 o 2 Fisso (Quota: {m['best_1x2'][2]})")
                    
        if not anomalie_trovate: st.success("Nessuna anomalia grave rilevata oggi.")

        st.markdown("---")
        st.markdown("<div class='strategy-box builder-bg'>", unsafe_allow_html=True)
        st.header("🧾 IL TUO CARRELLO MANUALE")
        
        # Somma di tutte le selezioni
        tutte_selezionate = sel_assoluta + sel_combo + sel_1x2 + sel_mg + sel_uo + sel_gg + sel_azzardo
        
        viste = set()
        carrello_finale = []
        for item in tutte_selezionate:
            chiave = f"{item['Match']}_{item['Tip']}"
            if chiave not in viste:
                viste.add(chiave)
                carrello_finale.append(item)

        if carrello_finale:
            q_tot_b, p_tot_b = 1.0, 1.0
            testo_scontrino = "=== CARRELLO MATRIX V91 ===\n\n"
            for pick in carrello_finale:
                st.write(f"✅ {pick['Match']}: **{pick['Tip']}** (Quota {pick['Quota']:.2f})")
                q_tot_b *= float(pick['Quota'])
                p_tot_b *= (float(pick['Prob']) / 100)
                testo_scontrino += f"[{pick['Time']}] {pick['Match']} -> {pick['Tip']} @ {pick['Quota']:.2f}\n"
            
            testo_scontrino += f"\n📊 QUOTA TOTALE: {q_tot_b:.2f}\n"
            testo_scontrino += f"🎯 PROBABILITÀ CONGIUNTA: {p_tot_b*100:.2f}%\n"
            
            st.write("---")
            cb1, cb2 = st.columns(2)
            cb1.metric("Quota Totale", f"{q_tot_b:.2f}")
            cb2.metric("Probabilità Congiunta", f"{p_tot_b*100:.2f}%")
            
            st.download_button(
                label="💾 SCARICA LA TUA SCHEDINA MANUALE",
                data=testo_scontrino,
                file_name=f"Matrix_CustomTicket_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain"
            )
        else:
            st.info("👆 Spunta qualche partita dalle classifiche qui sopra per costruire la tua schedina.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # TAB 2: GENERATORE SCHEDINE (CASSAFORTE + BUDGET)
    # ---------------------------------------------------------
    with t2:
        st.header("🏆 Generatore Algoritmico (Budget Ripartito)")
        
        # Ripartizione Vasi Comunicanti
        b_cassa = budget_totale * 0.55
        b_safe = budget_totale * 0.25
        b_perf = budget_totale * 0.15
        b_azz = budget_totale * 0.05
        
        testo_export = f"=== MATRIX V91: PIANO INVESTIMENTO ===\nBudget: {budget_totale}€ | Date: {start_str} / {end_str}\n\n"
        
        # 1. CASSAFORTE (1.10 - 1.30)
        st.markdown("<div style='padding: 15px; border-radius: 10px; background-color: #f8f9fa; border-left: 5px solid #2c3e50; margin-bottom: 20px;'>", unsafe_allow_html=True)
        st.subheader("🛡️ CASSAFORTE (Quota Target ~2.30)")
        st.markdown(f"**Puntata Allocata: {b_cassa:.2f}€ (55% del Budget)**")
        c_slip, q_tot_c, prob_c, usate_c = costruisci_schedina_dinamica(st.session_state.all_tips_global, 1.10, 1.30, target_mult=2.30, max_righe=8, is_cassaforte=True)
        testo_export += f"🛡️ CASSAFORTE (Puntata: {b_cassa:.2f}€)\n"
        for x in c_slip:
            st.write(f"• [{x['Time']}] {x['Match']}: **{x['Tip']}** (Q: {x['Quota']})")
            testo_export += f"- {x['Match']} -> {x['Tip']} @ {x['Quota']}\n"
        st.metric("Vincita Stimata (Copertura)", f"~{b_cassa * q_tot_c:.2f}€")
        testo_export += f"Vincita: ~{b_cassa * q_tot_c:.2f}€\n\n"
        st.markdown("</div>", unsafe_allow_html=True)

        # 2. SAFETY (1.31 - 1.50)
        st.markdown("<div class='strategy-box safety-bg'>", unsafe_allow_html=True)
        st.subheader("🟢 SAFETY (Quota Target ~2.30)")
        st.markdown(f"**Puntata Allocata: {b_safe:.2f}€ (25% del Budget)**")
        s_slip, q_tot_s, prob_s, usate_s = costruisci_schedina_dinamica(st.session_state.all_tips_global, 1.31, 1.50, target_mult=2.30, max_righe=5, escludi_match=usate_c, check_blacklist=True)
        testo_export += f"🟢 SAFETY (Puntata: {b_safe:.2f}€)\n"
        for x in s_slip:
            st.write(f"• [{x['Time']}] {x['Match']}: **{x['Tip']}** (Q: {x['Quota']})")
            testo_export += f"- {x['Match']} -> {x['Tip']} @ {x['Quota']}\n"
        st.metric("Vincita Stimata", f"~{b_safe * q_tot_s:.2f}€")
        testo_export += f"Vincita: ~{b_safe * q_tot_s:.2f}€\n\n"
        st.markdown("</div>", unsafe_allow_html=True)

        # 3. PERFORMANCE (1.51 - 2.20)
        st.markdown("<div class='strategy-box performance-bg'>", unsafe_allow_html=True)
        st.subheader("🟠 PERFORMANCE")
        st.markdown(f"**Puntata Allocata: {b_perf:.2f}€ (15% del Budget)**")
        p_slip, q_tot_p, prob_p, usate_p = costruisci_schedina_dinamica(st.session_state.all_tips_global, 1.51, 2.20, target_mult=5.0, max_righe=5, escludi_match=usate_s)
        testo_export += f"🟠 PERFORMANCE (Puntata: {b_perf:.2f}€)\n"
        for x in p_slip:
            st.write(f"• [{x['Time']}] {x['Match']}: **{x['Tip']}** (Q: {x['Quota']})")
            testo_export += f"- {x['Match']} -> {x['Tip']} @ {x['Quota']}\n"
        st.metric("Vincita Stimata", f"~{b_perf * q_tot_p:.2f}€")
        testo_export += f"Vincita: ~{b_perf * q_tot_p:.2f}€\n\n"
        st.markdown("</div>", unsafe_allow_html=True)

        # 4. AZZARDO (2.21 - 4.50)
        st.markdown("<div class='strategy-box risk-bg'>", unsafe_allow_html=True)
        st.subheader("🔴 AZZARDO")
        st.markdown(f"**Puntata Allocata: {b_azz:.2f}€ (5% del Budget)**")
        a_slip, q_tot_a, prob_a, _ = costruisci_schedina_dinamica(st.session_state.all_tips_global, 2.21, 4.50, target_mult=20.0, max_righe=5, escludi_match=usate_p)
        testo_export += f"🔴 AZZARDO (Puntata: {b_azz:.2f}€)\n"
        for x in a_slip:
            st.write(f"• [{x['Time']}] {x['Match']}: **{x['Tip']}** (Q: {x['Quota']})")
            testo_export += f"- {x['Match']} -> {x['Tip']} @ {x['Quota']}\n"
        st.metric("Vincita Stimata", f"~{b_azz * q_tot_a:.2f}€")
        testo_export += f"Vincita: ~{b_azz * q_tot_a:.2f}€\n\n"
        st.markdown("</div>", unsafe_allow_html=True)

        st.download_button("💾 SCARICA PIANO INVESTIMENTO", data=testo_export, file_name=f"Matrix_V91_Piano_{datetime.now().strftime('%Y%m%d')}.txt", mime="text/plain")

    # ---------------------------------------------------------
    # TAB 3: ESPLORATORE SINGOLE (Mantenuto identico per analisi chirurgica)
    # ---------------------------------------------------------
    with t3:
        st.write("Analisi chirurgica per le singole partite.")
        for camp, matches in st.session_state.data_master.items():
            with st.expander(f"🏆 {camp}", expanded=False):
                matches = sorted(matches, key=lambda x: x['orario'])
                for m in matches:
                    with st.expander(f"🕒 {m['orario']} | 🏟️ {m['c_u']} vs {m['t_u']}", expanded=False):
                        st.write(f"**Arbitro:** {m['arb']} | **VAR:** {'⚠️ Fiscale' if m['is_sev'] else '⚖️ Standard'} | **Clima:** {m['meteo']}")
                        
                        if m['msg_mot']: st.write(f"<span class='mot-testo'>{m['msg_mot']}</span>", unsafe_allow_html=True)
                        if m['andata_msg']: st.write(f"<span class='andata-testo'>{m['andata_msg']}</span>", unsafe_allow_html=True)
                        if m['streak_msg']: st.write(f"<span class='streak-testo'>{m['streak_msg']}</span>", unsafe_allow_html=True)
                        
                        st.markdown("<div class='stats-box'>", unsafe_allow_html=True)
                        col1, col2 = st.columns(2)
                        with col1:
                            mostra_rank_c = "" if camp in ["🇪🇺 Champions League", "🇪🇺 Europa League", "🇪🇺 Conference League"] else f" (Pos: {m['rank_c']}ª)"
                            st.write(f"🏠 **{m['c_s']}**{mostra_rank_c}")
                            st.write(f"📊 Stile: <span class='{'stile-orizzontale' if 'Orizz' in m['stile_c'] else 'stile-verticale'}'>{m['stile_c']}</span>", unsafe_allow_html=True)
                            st.write(f"⚽ Possesso: {m['poss_c']:.1f}% | 🎯 Tiri Area: {m['box_c']:.1f}")
                            st.write(f"🧤 Parate: {m['parate_c']:.1f} | 🛑 Falli: {m['falli_c']:.1f}")
                            st.write(f"🔪 Cinismo: **1 Gol ogni {m['conv_c']:.1f} tiri in porta**")
                            st.write(f"🛡️ Clean Sheet: <span class='cs-testo'>{m['cs_c']:.0f}%</span> | ❌ A secco: <span class='fts-testo'>{m['fts_c']:.0f}%</span>", unsafe_allow_html=True)
                        with col2:
                            mostra_rank_t = "" if camp in ["🇪🇺 Champions League", "🇪🇺 Europa League", "🇪🇺 Conference League"] else f" (Pos: {m['rank_t']}ª)"
                            st.write(f"✈️ **{m['t_s']}**{mostra_rank_t}")
                            st.write(f"📊 Stile: <span class='{'stile-orizzontale' if 'Orizz' in m['stile_t'] else 'stile-verticale'}'>{m['stile_t']}</span>", unsafe_allow_html=True)
                            st.write(f"⚽ Possesso: {m['poss_t']:.1f}% | 🎯 Tiri Area: {m['box_t']:.1f}")
                            st.write(f"🧤 Parate: {m['parate_t']:.1f} | 🛑 Falli: {m['falli_t']:.1f}")
                            st.write(f"🔪 Cinismo: **1 Gol ogni {m['conv_t']:.1f} tiri in porta**")
                            st.write(f"🛡️ Clean Sheet: <span class='cs-testo'>{m['cs_t']:.0f}%</span> | ❌ A secco: <span class='fts-testo'>{m['fts_t']:.0f}%</span>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)

                        c1, c2, c3, c4 = st.columns(4)
                        with c1:
                            st.markdown("<p class='label-bold'>XG Finale</p>", unsafe_allow_html=True)
                            st.metric(m['c_s'], f"{m['xg_c']:.2f}")
                            st.metric(m['t_s'], f"{m['xg_t']:.2f}")
                        with c2:
                            st.markdown("<p class='label-bold'>Forma & Riposo</p>", unsafe_allow_html=True)
                            st.write(f"🏠 <span class='form-box'>{m['forma_c']}</span> | {m['stan_c']}", unsafe_allow_html=True)
                            st.write(f"✈️ <span class='form-box'>{m['forma_t']}</span> | {m['stan_t']}", unsafe_allow_html=True)
                        with c3:
                            st.markdown("<p class='label-bold'>Assenti & V91 Radar</p>", unsafe_allow_html=True)
                            st.write(f"🏠 {m['msg_inf_c']}", unsafe_allow_html=True)
                            st.write(f"✈️ {m['msg_inf_t']}", unsafe_allow_html=True)
                        with c4: 
                            st.markdown("<p class='label-bold'>DNA Storico</p>", unsafe_allow_html=True)
                            st.write(f"<span class='dna-testo'>{m['dna_h2h']}</span>", unsafe_allow_html=True)

                        if m['best_1x2'][0] == "No Segno Fisso":
                            st.markdown(f"<div class='pure-1x2'>⚠️ NESSUN SEGNO SECCO CONSIGLIATO</div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div class='pure-1x2'>👑 Miglior Segno Secco: <b>{m['best_1x2'][0]}</b> ({m['best_1x2'][1]:.1f}%) | Quota: {m['best_1x2'][2]}</div>", unsafe_allow_html=True)
                        
                        exclude_safe = ["U4.5", "U5.5", "O0.5", "O1.5", "Casa O0.5", "Ospite O0.5"]
                        filtered_tips = {k: v for k, v in m['all_tips'].items() if k not in exclude_safe}
                        top_3 = sorted(filtered_tips.items(), key=lambda x: x[1], reverse=True)[:3]
                        
                        q1, _ = get_quota_finale(top_3[0][0], top_3[0][1], m['quote_reali'])
                        q2, _ = get_quota_finale(top_3[1][0], top_3[1][1], m['quote_reali'])
                        q3, _ = get_quota_finale(top_3[2][0], top_3[2][1], m['quote_reali'])

                        st.write("🎯 **TOP 3 ASSOLUTE DELLA PARTITA:**")
                        col_a, col_b, col_c = st.columns(3)
                        col_a.write(f"🥇 **{top_3[0][0]}** ({top_3[0][1]:.1f}%) Q: {q1}")
                        col_b.write(f"🥈 **{top_3[1][0]}** ({top_3[1][1]:.1f}%) Q: {q2}")
                        col_c.write(f"🥉 **{top_3[2][0]}** ({top_3[2][1]:.1f}%) Q: {q3}")
            
           
