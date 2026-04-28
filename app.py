import streamlit as st
import requests
import math
import pandas as pd
from datetime import datetime, timezone, timedelta
import pytz

# ==========================================
# 🎨 UI: TOTAL MATRIX DESIGN (V90 QUANTUM)
# ==========================================
st.set_page_config(page_title="Matrix Bet V90", page_icon="🎯", layout="wide")

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

# --- CONFIGURAZIONE E CAMPIONATI V90 ---
API_KEY_FOOTBALL = 'dc4d6488653c2d9a763290a44eb1613f'
STAGIONE = "2025"
HEADERS = {'x-apisports-key': API_KEY_FOOTBALL}

MASTER_LEAGUES = {
    # --- COPPE EUROPEE ---
    "🇪🇺 Champions League": 2, "🇪🇺 Europa League": 3, "🇪🇺 Conference League": 848,
    
    # --- TOP 5 EUROPEI & SECONDE LINEE ---
    "🇮🇹 Serie A": 135, "🇮🇹 Serie B": 136, 
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": 39, "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Championship": 40,
    "🇪🇸 La Liga": 140, "🇩🇪 Bundesliga": 78, "🇫🇷 Ligue 1": 61,
    
    # --- NUOVI TIER 2 EUROPEI (Miniera d'oro) ---
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 League One": 41, "🏴󠁧󠁢󠁥󠁮󠁧󠁿 League Two": 42,
    "🇳🇱 Eerste Divisie": 89, "🇩🇪 2. Bundesliga": 79, "🇪🇸 La Liga 2": 141,
    
    # --- ALTRI CAMPIONATI EUROPEI TRACCIATI ---
    "🇳🇱 Eredivisie": 88, "🇵🇹 Primeira Liga": 94, "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Prem.": 281,
    "🇹🇷 Süper Lig": 203, "🇧🇪 Pro League": 144, "🇬🇷 Super League": 197,
    "🇸🇪 Allsvenskan": 113, "🇳🇴 Eliteserien": 69, "🇫🇮 Veikkausliiga": 244,
    "🇩🇰 Superliga": 119, "🇨🇭 Super League": 207, "🇦🇹 Bundesliga": 218
}


# ==========================================
# 📡 MODULI API E CALCOLI MATEMATICI (V90)
# ==========================================
@st.cache_data(ttl=3600)
def get_active_leagues(start_date, end_date):
    active_ids = set()
    delta = end_date - start_date
    days = min(delta.days + 1, 7) 
    try:
        for i in range(days):
            d_str = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
            resp = requests.get("https://v3.football.api-sports.io/fixtures", headers=HEADERS, params={'date': d_str}).json()
            if 'response' in resp: active_ids.update({f['league']['id'] for f in resp['response']})
        return {k: v for k, v in MASTER_LEAGUES.items() if v in active_ids}
    except: return MASTER_LEAGUES

# V90: ESTRAZIONE DATI SINGOLO GIOCATORE (Rating, Posizione, Gol, Assist) - TOTALI
@st.cache_data(ttl=86400)
def get_player_advanced_stats(player_id, season):
    if not player_id: return "Unknown", 0, 0, 6.0, 0
    try:
        resp = requests.get("https://v3.football.api-sports.io/players", headers=HEADERS, params={'id': player_id, 'season': season}).json()
        if resp.get('response'):
            stats_array = resp['response'][0]['statistics']
            pos = "Unknown"
            tot_mins, tot_goals, tot_assists = 0, 0, 0
            ratings = []
            
            # Sommiamo le statistiche di tutte le competizioni (Campionato + Coppe)
            for stat in stats_array:
                if pos == "Unknown" and stat['games']['position']:
                    pos = stat['games']['position']
                tot_mins += stat['games']['minutes'] or 0
                tot_goals += stat['goals']['total'] or 0
                tot_assists += stat['goals']['assists'] or 0
                if stat['games']['rating']:
                    ratings.append(float(stat['games']['rating']))
            
            avg_rating = sum(ratings) / len(ratings) if ratings else 6.0
            return pos, tot_goals, tot_assists, avg_rating, tot_mins
    except: pass
    return "Unknown", 0, 0, 6.0, 0

# V90: IL NUOVO MOTORE ASSENTI AGNOSTICO (Basato su Minuti Assoluti)
def analizza_infortuni_pesati_v90(inf_list, season_lega):
    malus_att = 0.0  
    boost_opp = 0.0  
    t1_star, t2_rot, t3_ris, squalificati = 0, 0, 0, 0
    difensori_out = 0
    portiere_titolare_out = False
    visti = set()

    for i in inf_list:
        p_id = i['player'].get('id')
        if not p_id or p_id in visti: continue
        visti.add(p_id)
        
        motivo = str(i.get('type', '')).lower()
        if 'suspend' in motivo or 'red card' in motivo or 'card' in motivo:
            squalificati += 1

        # V90: Passiamo la stagione corretta alla ricerca del giocatore!
        pos, gol, assist, rating, mins = get_player_advanced_stats(p_id, season_lega)

        # Valutazione Assoluta V90: Evita il bug delle Coppe
        is_star = mins >= 1200 or rating >= 7.0

        if is_star: t1_star += 1
        elif mins >= 400: t2_rot += 1
        else: t3_ris += 1

        # L'IMPATTO AGNOSTICO SULL'ATTACCO
        if gol >= 5 or assist >= 5 or (pos in ["Attacker", "Midfielder"] and is_star):
            malus_att += 0.15
            if gol >= 10: malus_att += 0.10 
            if assist >= 8: malus_att += 0.10 
            if rating >= 7.3: malus_att += 0.10 

        # L'IMPATTO STRUTTURALE SULLA DIFESA
        if pos == "Defender":
            if is_star:
                boost_opp += 0.15
                difensori_out += 1
            elif mins >= 400:
                boost_opp += 0.05
                difensori_out += 1
        elif pos == "Goalkeeper":
            if is_star: 
                portiere_titolare_out = True
                boost_opp += 0.25 

    if difensori_out >= 2:
        boost_opp += 0.20 

    return min(0.60, malus_att), min(0.60, boost_opp), t1_star, t2_rot, t3_ris, len(visti), squalificati, portiere_titolare_out, difensori_out

@st.cache_data(ttl=3600)
def scarica_quote_native(league_id, date_str, season_lega):
    try:
        resp = requests.get("https://v3.football.api-sports.io/odds", headers=HEADERS, params={'league': league_id, 'season': season_lega, 'date': date_str, 'bookmaker': 8}).json()
        quote_dict = {}
        for item in resp.get('response', []):
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
    except: return {}

@st.cache_data(ttl=86400)
def analizza_statistiche_stagionali(league_id, team_id, season_lega):
    try:
        resp = requests.get("https://v3.football.api-sports.io/teams/statistics", headers=HEADERS, params={'league': league_id, 'season': season_lega, 'team': team_id}).json()
        stats = resp.get('response', {})
        if not stats: return 0.0, 0.0
        
        giocate = stats.get('fixtures', {}).get('played', {}).get('total', 0)
        if giocate == 0: return 0.0, 0.0
        
        cs_tot = stats.get('clean_sheet', {}).get('total', 0)
        fts_tot = stats.get('failed_to_score', {}).get('total', 0)
        
        cs_perc = (cs_tot / giocate) * 100
        fts_perc = (fts_tot / giocate) * 100
        return cs_perc, fts_perc
    except: return 0.0, 0.0

@st.cache_data(ttl=3600)
def analizza_statistiche_avanzate_pro(team_id):
    try:
        resp = requests.get("https://v3.football.api-sports.io/fixtures", headers=HEADERS, params={'team': team_id, 'last': 10, 'status': 'FT'}).json()
        matches = resp.get('response', [])
        
        tot_poss, tot_tiri, tot_tiri_area, tot_gol_fatti, tot_gol_subiti, tot_corner = 0, 0, 0, 0, 0, 0
        tot_cart, tot_falli, tot_parate = 0, 0, 0
        
        # V90 Fix: Due contatori separati. Uno per le statistiche, uno per i gol reali.
        match_v_stats = 0 
        match_v_goals = 0 
        squalificati_certi = 0 
        
        for i, m in enumerate(matches):
            fix_id = m['fixture']['id']
            is_home = str(m['teams']['home']['id']) == str(team_id)
            
            # --- CALCOLO GOL (FUORI DALLE STATISTICHE AVANZATE) ---
            # I gol vengono estratti dal tabellino base che esiste sempre!
            gf = m['goals']['home'] if is_home else m['goals']['away']
            gs = m['goals']['away'] if is_home else m['goals']['home']
            
            if gf is not None and gs is not None:
                tot_gol_fatti += int(gf)
                tot_gol_subiti += int(gs)
                match_v_goals += 1

            if i == 0:
                events_resp = requests.get("https://v3.football.api-sports.io/fixtures/events", headers=HEADERS, params={'fixture': fix_id}).json()
                if events_resp.get('response'):
                    for ev in events_resp['response']:
                        if str(ev['team']['id']) == str(team_id) and ev['type'] == 'Card' and 'Red' in ev.get('detail', ''):
                            squalificati_certi += 1

            # Recupero Statistiche Avanzate (se l'API non le ha, salta ma i gol sono già salvi)
            stats_resp = requests.get("https://v3.football.api-sports.io/fixtures/statistics", headers=HEADERS, params={'fixture': fix_id}).json()
            if stats_resp.get('response'):
                for t_stats in stats_resp['response']:
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
                        match_v_stats += 1
                        
        if match_v_stats == 0: match_v_stats = 1 
        if match_v_goals == 0: match_v_goals = 1 
        
        avg_poss = tot_poss / match_v_stats
        avg_tiri = tot_tiri / match_v_stats
        avg_tiri_area = tot_tiri_area / match_v_stats
        avg_corner = tot_corner / match_v_stats
        avg_cart = tot_cart / match_v_stats
        avg_falli = tot_falli / match_v_stats
        avg_parate = tot_parate / match_v_stats
        
        avg_gf = tot_gol_fatti / match_v_goals
        avg_gs = tot_gol_subiti / match_v_goals
        tiri_per_gol = avg_tiri / avg_gf if avg_gf > 0 else 10.0 
        
        if avg_poss > 55 and avg_tiri_area < 4: stile = "Tiki-Taka Sterile"
        elif avg_poss < 45 and avg_tiri_area > 4: stile = "Verticale Diretto"
        else: stile = "Bilanciato"
        
        return avg_poss, avg_tiri, avg_tiri_area, tiri_per_gol, avg_corner, avg_cart, avg_falli, avg_parate, stile, squalificati_certi, avg_gf, avg_gs
    except Exception as e: 
        return 50.0, 4.0, 5.0, 5.0, 4.5, 2.0, 10.0, 2.5, "Bilanciato", 0, 1.0, 1.0

def get_quota_finale(tip, prob, quote_reali):
    if quote_reali and tip in quote_reali: return quote_reali[tip], True
    if prob <= 0: return 50.0, False
    return max(1.01, round(1.0 + (((100 / prob) - 1.0) * 1.55), 2)), False

@st.cache_data(ttl=3600)
def analizza_squadra_globale(team_id):
    try:
        resp = requests.get("https://v3.football.api-sports.io/fixtures", headers=HEADERS, params={'team': team_id, 'last': 10, 'status': 'FT'}).json()
        matches = resp.get('response', [])
        if not matches: return 1.0, False, "N/D", 1.0, "Nessuno"
        
        ultima_data = datetime.strptime(matches[0]['fixture']['date'][:10], '%Y-%m-%d')
        diff_giorni = (datetime.now() - ultima_data).days
        is_stanca = diff_giorni <= 4
        m_stanchezza = 0.95 if is_stanca else 1.0
        
        forma_str, punti = "", 0
        
        for m in matches[:5]:
            is_home = str(m['teams']['home']['id']) == str(team_id)
            gh, ga = m['goals']['home'], m['goals']['away']
            if gh == ga: forma_str += "D"; punti += 1
            elif (is_home and gh > ga) or (not is_home and ga > gh): forma_str += "W"; punti += 3
            else: forma_str += "L"
        forma_str = forma_str[::-1] 
        m_forma = 0.9 + ((punti/15)*0.2)
        
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

        return m_stanchezza, is_stanca, forma_str, m_forma, (", ".join(ritardi) if ritardi else "Nessuno")
    except: return 1.0, False, "N/D", 1.0, "Nessuno"

@st.cache_data(ttl=3600)
def analizza_h2h_dna_e_andata(id_casa, id_trasf):
    try:
        resp = requests.get("https://v3.football.api-sports.io/fixtures/headtohead", headers=HEADERS, params={'h2h': f"{id_casa}-{id_trasf}", 'last': 5}).json()
        matches = resp.get('response', [])
        if not matches: return 1.0, 1.0, 0, 0, "Nessun Precedente", 1.0, 1.0, "", "Nessun match."
        
        vittorie_c, vittorie_t, gol_c, gol_t = 0, 0, 0, 0
        andata_msg, boost_andata_c, boost_andata_t = "", 1.0, 1.0
        
        dettagli_list = []
        for m in matches:
            if m['goals']['home'] is not None:
                d_m = datetime.strptime(m['fixture']['date'][:10], '%Y-%m-%d').strftime('%d/%m/%Y')
                dettagli_list.append(f"📅 {d_m}: {m['teams']['home']['name']} <b>{m['goals']['home']} - {m['goals']['away']}</b> {m['teams']['away']['name']}")
        dettagli_str = "<br>".join(dettagli_list) if dettagli_list else "Nessun match."
        
        ultimo_match = matches[0]
        data_ultimo = datetime.strptime(ultimo_match['fixture']['date'][:10], '%Y-%m-%d')
        if (datetime.now() - data_ultimo).days <= 28:
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
        
        for m in matches:
            if m['goals']['home'] is None: continue
            is_home_now = m['teams']['home']['id'] == id_casa
            gc, gt = (m['goals']['home'], m['goals']['away']) if is_home_now else (m['goals']['away'], m['goals']['home'])
            gol_c += gc; gol_t += gt
            if gc > gt: vittorie_c += 1
            elif gt > gc: vittorie_t += 1
            
        m_count = max(1, len([m for m in matches if m['goals']['home'] is not None]))
        m_h2h_c = min(1.20, max(0.80, 0.90 + (vittorie_c/m_count)*0.20 + (gol_c/(m_count*max(1, gol_c+gol_t)))*0.10))
        m_h2h_t = min(1.20, max(0.80, 0.90 + (vittorie_t/m_count)*0.20 + (gol_t/(m_count*max(1, gol_c+gol_t)))*0.10))
        
        storico_str = f"Vittorie: 🏠 {vittorie_c} - {vittorie_t} ✈️ | Gol H2H: {gol_c} a {gol_t}"
        return m_h2h_c, m_h2h_t, gol_c, gol_t, storico_str, boost_andata_c, boost_andata_t, andata_msg, dettagli_str
    except: return 1.0, 1.0, 0, 0, "Dati N/D", 1.0, 1.0, "", "Nessun dato."

@st.cache_data(ttl=3600)
def scarica_meteo(citta):
    try:
        url = f"https://wttr.in/{citta}?format=j1"
        resp = requests.get(url, timeout=3).json()
        cond = resp['current_condition'][0]['weatherDesc'][0]['value']
        pioggia = any(p in cond.lower() for p in ['rain', 'snow', 'shower', 'thunder'])
        return (0.90, f"🌧️ {cond}") if pioggia else (1.0, f"☀️ {cond}")
    except: return 1.0, "🌥️ Dato N/D"

def calcola_prob_poisson(xg, gol): return ((xg ** gol) * math.exp(-xg)) / math.factorial(gol)

def calcola_tutti_i_mercati(xg_c, xg_t, avg_corner_match, avg_cart_match, is_sev, tot_falli_match):
    p = {"1":0,"X":0,"2":0,"1X":0,"X2":0,"12":0,"Goal":0,"NoGoal":0, "Pari":0, "Dispari":0}
    mg = {"MG 1-3":0, "MG 1-4":0, "MG 2-3":0, "MG 2-4":0, "MG 2-5":0, "MG 3-4":0}
    uo_lines = [1.5, 2.5, 3.5, 4.5]
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
            
            if gc <= 4 and gt <= 4: re_prob[f"Risultato {gc}-{gt}"] = prob

    p["1X"], p["X2"], p["12"] = (p["1"]+p["X"]), (p["X"]+p["2"]), (p["1"]+p["2"])

    if xg_c > 1.2 and xg_t > 1.2:
        p["Goal"] = min(90.0, p["Goal"] * 1.18) 
        p["NoGoal"] = 100 - p["Goal"]
    elif xg_c < 0.9 and xg_t < 0.9:
        p["NoGoal"] = min(90.0, p["NoGoal"] * 1.15)
        p["Goal"] = 100 - p["NoGoal"]

    combos = {
        "1X + Over 1.5": p["1X"] * (p["O1.5"]/100) * 0.92,
        "X2 + Over 1.5": p["X2"] * (p["O1.5"]/100) * 0.92,
        "1X + Under 3.5": p["1X"] * (p["U3.5"]/100) * 0.95,
        "X2 + Under 3.5": p["X2"] * (p["U3.5"]/100) * 0.95,
        "1 + Over 2.5": p["1"] * (p["O2.5"]/100) * 0.90,
        "2 + Over 2.5": p["2"] * (p["O2.5"]/100) * 0.90,
        "Goal + Over 2.5": p["Goal"] * (p["O2.5"]/100) * 0.95
    }

    ht_prob = {"1": p["1"]*0.9, "X": p["X"]*1.5, "2": p["2"]*0.9} 
    tot_ht = sum(ht_prob.values()); ht_prob = {k: v/tot_ht for k,v in ht_prob.items()}
    htft = {}
    for ht in ["1", "X", "2"]:
        for ft in ["1", "X", "2"]: htft[f"HT/FT {ht}/{ft}"] = (ht_prob[ht] * p[ft]) 

    prob_corner_85 = min(92.0, max(15.0, (avg_corner_match / 9.5) * 55))
    tension = avg_cart_match + (1.5 if is_sev else 0) + (tot_falli_match / 20.0) 
    prob_cart_45 = min(88.0, max(20.0, (tension / 5.0) * 55))

    special = {
        "Over 8.5 Angoli": prob_corner_85,
        "Over 4.5 Cartellini": prob_cart_45
    }

    return {**p, **mg, **re_prob, **combos, **htft, **special}

def semplifica_nome(nome):
    for p in ['FC', 'AC ', ' BC', ' AS', ' Calcio', 'AFC ', 'SL ']: 
        nome = nome.replace(p, '')
    return nome.strip()

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

def costruisci_schedina_dinamica(pool, min_q, max_q, target_mult, escludi_match=None, max_match_q=5.0, max_righe=12, max_same_family=2):
    if escludi_match is None: escludi_match = set()
    valid = [x for x in pool if min_q <= float(x['Quota']) <= max_q and float(x['Quota']) <= max_match_q]
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
# 🏠 LOGICA DI STATO E INTERFACCIA
# ==========================================
if 'data_master' not in st.session_state: st.session_state.data_master = {}
if 'all_tips_global' not in st.session_state: st.session_state.all_tips_global = []

st.sidebar.header("⚙️ Centrale Operativa V90")

date_range = st.sidebar.date_input("Seleziona Periodo (Dal - Al):", [])
if len(date_range) == 2: start_date, end_date = date_range[0], date_range[1]
elif len(date_range) == 1: start_date = end_date = date_range[0]
else: start_date = end_date = datetime.now().date()

start_str = start_date.strftime('%Y-%m-%d')
end_str = end_date.strftime('%Y-%m-%d')

st.sidebar.markdown("---")
budget_totale = st.sidebar.number_input("💰 Budget Totale da Investire (€):", min_value=5.0, value=50.0, step=5.0)
st.sidebar.markdown("---")

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ SVUOTA MEMORIA V90 (Hard Reset)"):
    st.cache_data.clear()
    st.session_state.data_master = {}
    st.session_state.all_tips_global = []
    st.sidebar.success("✅ Cache svuotata! Il sistema è pronto per una scansione pulita.")
st.sidebar.markdown("---")

with st.sidebar:
    if st.button("🔍 Trova Campionati Attivi nel Periodo"):
        with st.spinner("Scansione palinsesto in corso..."):
            st.session_state['active_leagues'] = get_active_leagues(start_date, end_date)

if 'active_leagues' not in st.session_state: st.session_state['active_leagues'] = MASTER_LEAGUES 
active_dict = st.session_state['active_leagues']
if not active_dict: st.sidebar.warning("Nessun campionato supportato attivo.")
scelte = st.sidebar.multiselect("Campionati in campo:", list(active_dict.keys()), default=list(active_dict.keys()))

btn_genera = st.sidebar.button("⚡ ESTRAI MATRIX V90")

if btn_genera:
    st.session_state.data_master = {}
    st.session_state.all_tips_global = []
    now_utc = datetime.now(timezone.utc)
    tz_ita = pytz.timezone('Europe/Rome')
    mese_attuale = datetime.now().month

    for name in scelte:
        f_id = active_dict[name]
        with st.spinner(f"Analisi V90 (Motore Giocatori & Rating) {name}..."):
            
            # ==========================================
            # V90 SMART CALENDAR (Nordiche = Anno Solare, Altre = STAGIONE)
            # ==========================================
            is_lega_estiva = name in ["🇸🇪 Allsvenskan", "🇳🇴 Eliteserien", "🇫🇮 Veikkausliiga"]
            stagione_lega = start_date.year if is_lega_estiva else STAGIONE

            fix = requests.get("https://v3.football.api-sports.io/fixtures", headers=HEADERS, params={'league': f_id, 'season': stagione_lega, 'from': start_str, 'to': end_str}).json()
            std = requests.get("https://v3.football.api-sports.io/standings", headers=HEADERS, params={'league': f_id, 'season': stagione_lega}).json()
            
            if not fix.get('response'): continue

            db_stats = {}
            punti_champions, punti_salvezza, tot_squadre, partite_totali_campionato = 0, 0, 20, 38
            
            # Se la classifica esiste, la leggiamo normalmente
            if std.get('response') and len(std['response']) > 0 and 'league' in std['response'][0] and 'standings' in std['response'][0]['league']:
                tutti_i_gironi = std['response'][0]['league']['standings']
                for gruppo in tutti_i_gironi:
                    tot_squadre = len(gruppo)
                    for t in gruppo:
                        n = semplifica_nome(t['team']['name'])
                        db_stats[n] = {
                            'id': t['team']['id'], 'rank': t['rank'], 'giocate': t['all']['played'], 'punti': t['points'],
                            'ac': t['home']['goals']['for'] / max(1, t['home']['played']),
                            'dc': t['home']['goals']['against'] / max(1, t['home']['played']),
                            'at': t['away']['goals']['for'] / max(1, t['away']['played']),
                            'dt': t['away']['goals']['against'] / max(1, t['away']['played'])
                        }
            else:
                # [V90 STANDINGS FALLBACK] Classifica vuota dall'API? Nessun problema.
                # Creiamo un database di emergenza leggendo le squadre direttamente dalle partite in programma.
                for f in fix['response']:
                    for team_type in ['home', 'away']:
                        t_u = f['teams'][team_type]['name']
                        t_id = f['teams'][team_type]['id']
                        n = semplifica_nome(t_u)
                        if n not in db_stats:
                            db_stats[n] = {
                                'id': t_id, 'rank': 10, 'giocate': 0, 'punti': 0,
                                'ac': 0.0, 'dc': 0.0, 'at': 0.0, 'dt': 0.0
                            }

            matches_list = []
            date_giocate = {f['fixture']['date'][:10] for f in fix['response']}
            odds_cache = {}
            for d_match in date_giocate:
                # Passiamo la stagione dinamica per scaricare le quote corrette
                odds_cache[d_match] = scarica_quote_native(f_id, d_match, stagione_lega)

            for f in fix['response']:
                if f['fixture']['status']['short'] in ['PST', 'CANC', 'ABD', 'AWD', 'WO']: continue 

                fix_id = f['fixture']['id']
                match_date_str = f['fixture']['date'][:10]
                match_time_utc = datetime.fromisoformat(f['fixture']['date'])
                if match_time_utc <= now_utc: continue
                match_time_ita = match_time_utc.astimezone(tz_ita)
                orario_ita = match_time_ita.strftime('%d/%m %H:%M')

                c_u, t_u = f['teams']['home']['name'], f['teams']['away']['name']
                c_s, t_s = semplifica_nome(c_u), semplifica_nome(t_u)
                # ==========================================
                # V90 PLAYOFF RESCUE: Recupero squadre fuori classifica
                # ==========================================
                # Se le squadre giocano i playoff e non sono nella classifica principale, 
                # le aggiungiamo al volo al database con 0 partite. Il Sensore Inizio Stagione 
                # riconoscerà lo 0 e calcolerà l'xG basandosi al 100% sullo storico recente!
                if c_s not in db_stats:
                    db_stats[c_s] = {'id': f['teams']['home']['id'], 'rank': 10, 'giocate': 0, 'punti': 0, 'ac': 0.0, 'dc': 0.0, 'at': 0.0, 'dt': 0.0}
                if t_s not in db_stats:
                    db_stats[t_s] = {'id': f['teams']['away']['id'], 'rank': 10, 'giocate': 0, 'punti': 0, 'ac': 0.0, 'dc': 0.0, 'at': 0.0, 'dt': 0.0}
                # ==========================================

                quote_reali_match = odds_cache.get(match_date_str, {}).get(fix_id, {})
                

                m_st_c, is_stanca_c, forma_c, m_f_c, rit_c = analizza_squadra_globale(db_stats[c_s]['id'])
                m_st_t, is_stanca_t, forma_t, m_f_t, rit_t = analizza_squadra_globale(db_stats[t_s]['id'])
                
                cs_c, fts_c = analizza_statistiche_stagionali(f_id, db_stats[c_s]['id'], stagione_lega)
                cs_t, fts_t = analizza_statistiche_stagionali(f_id, db_stats[t_s]['id'], stagione_lega)
                
                m_met, d_met = scarica_meteo(c_s)
                m_h2h_c, m_h2h_t, gol_h2h_c, gol_h2h_t, str_h2h, b_and_c, b_and_t, andata_msg, dettagli_h2h_str = analizza_h2h_dna_e_andata(db_stats[c_s]['id'], db_stats[t_s]['id'])

                # ---> SPOSTATE QUI IN ALTO: Estrazione a 12 variabili <---
                poss_c, tiri_c, box_c, conv_c, corn_c, cart_c, falli_c, parate_c, stile_c, sq_certi_c, gf_10_c, gs_10_c = analizza_statistiche_avanzate_pro(db_stats[c_s]['id'])
                poss_t, tiri_t, box_t, conv_t, corn_t, cart_t, falli_t, parate_t, stile_t, sq_certi_t, gf_10_t, gs_10_t = analizza_statistiche_avanzate_pro(db_stats[t_s]['id'])
                
                # ==========================================
                # INIZIO BLOCCO INFORTUNI V90 PRO (BLINDATO)
                # ==========================================
                c_id = db_stats[c_s]['id']
                t_id = db_stats[t_s]['id']
                
                # Definiamo le leghe "cieche" per risparmiare API e attivare la modalità 100% Statistica
                is_lega_cieca = f_id in [41, 42] # 41: League One, 42: League Two
                msg_radar = "⚠️ Radar Infortuni Offline (Lega Minore) - Algoritmo 100% Statistico" if is_lega_cieca else ""
                
                if is_lega_cieca:
                    # NESSUNA chiamata API. Risparmiamo quota e azzeriamo le variabili di malus.
                    malus_att_c, boost_opp_c, t1_c, t2_c, t3_c, count_c, sq_c, gk_out_c, def_out_c = 0.0, 0.0, 0, 0, 0, 0, 0, False, 0
                    malus_att_t, boost_opp_t, t1_t, t2_t, t3_t, count_t, sq_t, gk_out_t, def_out_t = 0.0, 0.0, 0, 0, 0, 0, 0, False, 0
                    
                    # Applichiamo solo il "Radar Squalifiche Estremo" se abbiamo intercettato rossi dalle stats
                    if sq_certi_c > 0:
                        sq_c += sq_certi_c; count_c += sq_certi_c; malus_att_c += (0.05 * sq_certi_c)
                    if sq_certi_t > 0:
                        sq_t += sq_certi_t; count_t += sq_certi_t; malus_att_t += (0.05 * sq_certi_t)
                else:
                    # Chiamata base per Fixture (Solo per le leghe tracciate)
                    inj_resp = requests.get("https://v3.football.api-sports.io/injuries", headers=HEADERS, params={'fixture': fix_id}).json()
                    inf_all = inj_resp.get('response', [])
                    if not isinstance(inf_all, list): inf_all = []
                    
                    # [RETE LARGA] Se è una coppa e l'array è vuoto, forziamo la ricerca
                    if len(inf_all) == 0:
                        inj_fall_c = requests.get("https://v3.football.api-sports.io/injuries", headers=HEADERS, params={'team': c_id, 'date': match_date_str}).json()
                        inj_fall_t = requests.get("https://v3.football.api-sports.io/injuries", headers=HEADERS, params={'team': t_id, 'date': match_date_str}).json()
                        if isinstance(inj_fall_c.get('response'), list): inf_all.extend(inj_fall_c['response'])
                        if isinstance(inj_fall_t.get('response'), list): inf_all.extend(inj_fall_t['response'])
                    
                    inf_c_list = [i for i in inf_all if str(i['team']['id']) == str(c_id)]
                    inf_t_list = [i for i in inf_all if str(i['team']['id']) == str(t_id)]
                    
                    malus_att_c, boost_opp_c, t1_c, t2_c, t3_c, count_c, sq_c, gk_out_c, def_out_c = analizza_infortuni_pesati_v90(inf_c_list, stagione_lega)
                    malus_att_t, boost_opp_t, t1_t, t2_t, t3_t, count_t, sq_t, gk_out_t, def_out_t = analizza_infortuni_pesati_v90(inf_t_list, stagione_lega)
                    
                    # [RADAR SQUALIFICHE] Aggiungiamo i rossi matematici se l'API non li ha visti
                    if sq_certi_c > 0 and sq_c == 0:
                        sq_c += sq_certi_c; count_c += sq_certi_c; malus_att_c += (0.05 * sq_certi_c)
                    if sq_certi_t > 0 and sq_t == 0:
                        sq_t += sq_certi_t; count_t += sq_certi_t; malus_att_t += (0.05 * sq_certi_t)
                # ==========================================
                # FINE BLOCCO INFORTUNI V90 PRO (BLINDATO)
                # ==========================================
                # ==========================================
                # V90: SQUAD DEPTH BUFFER (Sindrome di Golia)
                # ==========================================
                # Risolve l'anomalia delle Big (Inter, Fenerbahçe, ecc.) che venivano
                # iper-penalizzate dagli assenti contro le piccole. La panchina di una Big 
                # è superiore ai titolari di una piccola, quindi assorbiamo il malus.
                
                # Definiamo al volo se è una coppa per evitare il NameError
                is_coppa_check = name in ["🇪🇺 Champions League", "🇪🇺 Europa League", "🇪🇺 Conference League"]
                
                if not is_coppa_check:
                    punti_c_depth = db_stats[c_s]['punti']
                    punti_t_depth = db_stats[t_s]['punti']
                    gap_c = punti_c_depth - punti_t_depth
                    gap_t = punti_t_depth - punti_c_depth
                    
                    # Se la squadra in Casa ha almeno 15 punti di vantaggio (È Golia)
                    if gap_c >= 15:
                        ammortizzatore = max(0.20, 1.0 - (gap_c / 45.0)) 
                        malus_att_c *= ammortizzatore
                        boost_opp_t *= ammortizzatore
                        
                    # Se la squadra in Trasferta ha almeno 15 punti di vantaggio (È Golia)
                    elif gap_t >= 15:
                        ammortizzatore = max(0.20, 1.0 - (gap_t / 45.0))
                        malus_att_t *= ammortizzatore
                        boost_opp_c *= ammortizzatore
                # ==========================================
                streak_breaker_c = (gol_h2h_c == 0) and (count_t > 0 or is_stanca_t)
                streak_breaker_t = (gol_h2h_t == 0) and (count_c > 0 or is_stanca_c)
                
               
                is_coppa = name in ["🇪🇺 Champions League", "🇪🇺 Europa League", "🇪🇺 Conference League"]
                m_mot_c, m_mot_t, tension_idx = 1.0, 1.0, 1.0
                msg_mot = ""

                if is_coppa and mese_attuale in [3, 4, 5]:
                    m_mot_c, m_mot_t = 1.25, 1.25 
                    tension_idx += 0.3
                    msg_mot = "🔥 DENTRO O FUORI (Coppa)"
                elif not is_coppa:
                    punti_disp_c = (partite_totali_campionato - db_stats[c_s]['giocate']) * 3
                    punti_disp_t = (partite_totali_campionato - db_stats[t_s]['giocate']) * 3
                    punti_c = db_stats[c_s]['punti']
                    punti_t = db_stats[t_s]['punti']
                    rank_c = db_stats[c_s]['rank']
                    rank_t = db_stats[t_s]['rank']

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

               # ==========================================
                # V90 HYBRID XG CORE (Risolve il bug delle quote sballate)
                # ==========================================
                # 1. XG puramente dalla Classifica/Girone attuale
                xg_standings_c = math.sqrt(max(0.01, db_stats[c_s]['ac']) * max(0.01, db_stats[t_s]['dt']))
                xg_standings_t = math.sqrt(max(0.01, db_stats[t_s]['at']) * max(0.01, db_stats[c_s]['dc']))

                # 2. XG Momentum dalle ultime 10 partite (copre i buchi statistici delle coppe)
                xg_momentum_c = math.sqrt(max(0.01, gf_10_c) * max(0.01, gs_10_t))
                xg_momentum_t = math.sqrt(max(0.01, gf_10_t) * max(0.01, gs_10_c))

                # Nelle Coppe o Leghe Minori, il Momentum pesa l'80% perché le classifiche sono troppo corte o volatili.
                # Nei Campionati normali, ci affidiamo al 70% alla classifica stagionale e al 30% allo stato di forma recente.
                # V90 EARLY SEASON SENSOR: Se hanno giocato 5 partite o meno, la classifica è acerba. Usa il Momentum all'80%.
                partite_giocate_casa = db_stats[c_s]['giocate']
                peso_momentum = 0.80 if (is_coppa_check or partite_giocate_casa <= 5) else 0.30
                peso_standings = 1.0 - peso_momentum

                # 3. Fusione finale
                xg_base_c = ((xg_standings_c * peso_standings) + (xg_momentum_c * peso_momentum)) * m_f_c * m_st_c
                xg_base_t = ((xg_standings_t * peso_standings) + (xg_momentum_t * peso_momentum)) * m_f_t * m_st_t
                # ==========================================
                
                malus_league = 1.0
                if name in ["🇬🇷 Super League", "🇫🇷 Ligue 1", "🇮🇹 Serie B"]: malus_league = 0.85 
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

                if fts_c > 35.0: xg_base_c *= 0.85 
                if cs_t > 35.0: xg_base_c *= 0.85  
                if fts_t > 35.0: xg_base_t *= 0.85
                if cs_c > 35.0: xg_base_t *= 0.85
                
                se_sgombra_c = "C. Sgombra" in msg_mot
                se_sgombra_t = "O. Sgombra" in msg_mot
                
                # V90: INCROCIO TOTALE xG. 
                # Casa perde xG se manca il suo bomber (malus_att_c). 
                # Casa guadagna xG se manca il difensore avversario (boost_opp_t)
                xg_c = xg_base_c * (1 - malus_att_c) * (1 + boost_opp_t) * m_h2h_c * b_and_c * m_mot_c * (1.10 if se_sgombra_t else 1.0)
                xg_t = xg_base_t * (1 - malus_att_t) * (1 + boost_opp_c) * m_h2h_t * b_and_t * m_mot_t * (1.10 if se_sgombra_c else 1.0)
                
                msg_streak = ""
                if streak_breaker_c: xg_c = max(1.15, xg_c * 1.45); msg_streak += "🔥 STREAK CASA "
                if streak_breaker_t: xg_t = max(1.15, xg_t * 1.45); msg_streak += "🔥 STREAK OSPITE"
                
                xg_c *= m_met; xg_t *= m_met
                
                arb = f['fixture']['referee'] or "N/D"
                is_sev = any(s in str(arb) for s in ["Orsato", "Maresca", "Taylor", "Oliver", "Lahoz", "Hernandez"])
                m_arb = 1.05 if is_sev else 1.0
                xg_c *= m_arb; xg_t *= m_arb
                
                avg_corner_match = corn_c + corn_t
                avg_cart_match = cart_c + cart_t

                full_tips = calcola_tutti_i_mercati(xg_c, xg_t, avg_corner_match, avg_cart_match, is_sev, tot_falli_match)
                
                best_1x2_key = max(["1", "X", "2"], key=lambda k: full_tips[k])
                if full_tips[best_1x2_key] < 45.0:
                    best_1x2_key = "No Segno Fisso"
                    best_1x2_prob = 0.0
                    best_1x2_q = "-"
                    best_1x2_real = False
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
                    "count_c": count_c, "sq_c": sq_c, "t1_c": t1_c, "t2_c": t2_c, "t3_c": t3_c, "gk_out_c": gk_out_c, "def_out_c": def_out_c,
                    "count_t": count_t, "sq_t": sq_t, "t1_t": t1_t, "t2_t": t2_t, "t3_t": t3_t, "gk_out_t": gk_out_t, "def_out_t": def_out_t,
                    "meteo": d_met,"msg_radar": msg_radar, "dna_h2h": str_h2h, "dettagli_h2h": dettagli_h2h_str, "streak_msg": msg_streak.strip(), "andata_msg": andata_msg, "msg_mot": msg_mot.strip(),
                    "stan_c": "⚠️ Fatigue" if is_stanca_c else "✅ Riposo", "stan_t": "⚠️ Fatigue" if is_stanca_t else "✅ Riposo", 
                    "forma_c": forma_c, "forma_t": forma_t, "rit_c": rit_c, "rit_t": rit_t,
                    "poss_c": poss_c, "tiri_c": tiri_c, "conv_c": conv_c, "stile_c": stile_c,
                    "box_c": box_c, "falli_c": falli_c, "parate_c": parate_c,
                    "poss_t": poss_t, "tiri_t": tiri_t, "conv_t": conv_t, "stile_t": stile_t,
                    "box_t": box_t, "falli_t": falli_t, "parate_t": parate_t,
                    "corn_tot": avg_corner_match, "cart_tot": avg_cart_match, "falli_tot": tot_falli_match
                })
            if matches_list: st.session_state.data_master[name] = matches_list

# --- DISPLAY DELLE 3 TAB ---
if st.session_state.data_master:
    t1, t2, t3 = st.tabs(["🛒 TOP 10 & BUILDER", "🔬 ESPLORATORE PARTITE", "🏆 SCHEDINE AUTOMATICHE"])
    
    with t1:
        st.header("🛒 BET BUILDER & CLASSIFICHE OMNI-MARKET")
        st.write("Spunta la casella '🛒' nelle tabelle qui sotto per aggiungere la partita al tuo Carrello (calcolato automaticamente a fine pagina).")

        def mostra_tabella_interattiva(titolo, tip_filters, min_q=1.01, max_rows=10):
            st.subheader(titolo)
            pool = [x for x in st.session_state.all_tips_global if (tip_filters(x['Tip']) if callable(tip_filters) else x['Tip'] in tip_filters) and float(x['Quota']) >= min_q]
            if not pool:
                st.info("Nessun dato disponibile per questa categoria.")
                return []
            
            df = pd.DataFrame(pool).sort_values(by="Prob", ascending=False).head(max_rows)
            df = df[['Match', 'Tip', 'Prob', 'Quota', 'Time', 'League']]
            df.insert(0, "🛒", False) 
            
            edited_df = st.data_editor(
                df,
                column_config={
                    "🛒": st.column_config.CheckboxColumn("Seleziona", default=False),
                    "Prob": st.column_config.NumberColumn("Probabilità (%)", format="%.1f%%"),
                    "Quota": st.column_config.NumberColumn("Quota", format="%.2f")
                },
                hide_index=True,
                use_container_width=True,
                disabled=['Match', 'Tip', 'Prob', 'Quota', 'Time', 'League'],
                key=f"editor_{titolo}"
            )
            return edited_df[edited_df["🛒"] == True].to_dict('records')

        sel_1 = mostra_tabella_interattiva("👑 Top 10 Assoluta (No U4.5/O0.5)", lambda tip: tip not in ["U4.5", "Casa O0.5", "Ospite O0.5"])
        sel_2 = mostra_tabella_interattiva("🛡️ Top 10 Doppie Chance", ["1X", "X2", "12"])
        sel_3 = mostra_tabella_interattiva("⚽ Top 10 Over / Under", lambda tip: tip.startswith("O") or tip.startswith("U"))
        sel_4 = mostra_tabella_interattiva("🎯 Top 10 Goal / NoGoal", ["Goal", "NoGoal"])
        
        # NUOVE TABELLE V90: Multigol e Combo Match (Sostituiscono l'HT/FT)
        sel_mg = mostra_tabella_interattiva("🥅 Top 10 Multigol", lambda tip: tip.startswith("MG"))
        sel_combo = mostra_tabella_interattiva("🧩 Top 10 Combo Match", lambda tip: "+" in tip)
        
        sel_6 = mostra_tabella_interattiva("🧨 Top 10 Azzardi (Quote Alte >= 2.50)", lambda tip: True, min_q=2.50)
        
        # Carrello aggiornato con le nuove liste
        tutte_selezionate = sel_1 + sel_2 + sel_3 + sel_4 + sel_mg + sel_combo + sel_6
        
        viste = set()
        carrello_finale = []
        for item in tutte_selezionate:
            chiave = f"{item['Match']}_{item['Tip']}"
            if chiave not in viste:
                viste.add(chiave)
                carrello_finale.append(item)

        st.markdown("---")
        st.markdown("<div class='strategy-box builder-bg'>", unsafe_allow_html=True)
        st.header("🧾 IL TUO CARRELLO")
        if carrello_finale:
            q_tot_b, p_tot_b = 1.0, 1.0
            testo_scontrino = "=== RICEVUTA MATRIX V90 ===\n\n"
            
            for pick in carrello_finale:
                st.write(f"✅ {pick['Match']}: **{pick['Tip']}** (Quota {pick['Quota']:.2f})")
                q_tot_b *= float(pick['Quota'])
                p_tot_b *= (float(pick['Prob']) / 100)
                testo_scontrino += f"[{pick['Time']}] {pick['Match']} -> {pick['Tip']} @ {pick['Quota']:.2f}\n"
            
            testo_scontrino += f"\n📊 QUOTA TOTALE: {q_tot_b:.2f}\n"
            testo_scontrino += f"🎯 PROBABILITÀ CONGIUNTA: {p_tot_b*100:.2f}%\n"
            testo_scontrino += f"💰 VINCITA STIMATA (su {budget_totale}€): ~{budget_totale * q_tot_b:.2f}€\n"
            
            st.write("---")
            cb1, cb2, cb3 = st.columns(3)
            cb1.metric("Quota Totale", f"{q_tot_b:.2f}")
            cb2.metric("Probabilità Congiunta", f"{p_tot_b*100:.2f}%")
            cb3.metric(f"Vincita (su Budget Tot. {budget_totale}€)", f"~{budget_totale * q_tot_b:.2f}€")
            
            st.download_button(
                label="💾 SCARICA / SALVA SCHEDINA (TXT)",
                data=testo_scontrino,
                file_name=f"Matrix_Ticket_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain"
            )
        else:
            st.info("👆 Spunta qualche partita dalle classifiche qui sopra per costruire la schedina in tempo reale.")
        st.markdown("</div>", unsafe_allow_html=True)

    with t2:
        st.write(f"Partite UFFICIALI V90 per il periodo **{start_str} / {end_str}**.")
        for camp, matches in st.session_state.data_master.items():
            with st.expander(f"🏆 {camp}", expanded=False):
                matches = sorted(matches, key=lambda x: x['orario'])
                for m in matches:
                    with st.expander(f"🕒 {m['orario']} | 🏟️ {m['c_u']} vs {m['t_u']}", expanded=False):
                        st.write(f"**Arbitro:** {m['arb']} | **VAR:** {'⚠️ Fiscale' if m['is_sev'] else '⚖️ Standard'} | **Clima:** {m['meteo']}")
                        
                        if m['msg_mot']: st.write(f"<span class='mot-testo'>{m['msg_mot']}</span>", unsafe_allow_html=True)
                        if m['andata_msg']: st.write(f"<span class='andata-testo'>{m['andata_msg']}</span>", unsafe_allow_html=True)
                        if m['streak_msg']: st.write(f"<span class='streak-testo'>{m['streak_msg']}</span>", unsafe_allow_html=True)
                        if m.get('msg_radar'): st.warning(m['msg_radar'])
                        
                        st.markdown("<div class='stats-box'>", unsafe_allow_html=True)
                        col1, col2 = st.columns(2)
                        with col1:
                            # Nascondiamo la Posizione Classifica nelle Coppe per non confondere
                            mostra_rank_c = "" if camp in ["🇪🇺 Champions League", "🇪🇺 Europa League", "🇪🇺 Conference League"] else f" (Pos: {m['rank_c']}ª)"
                            st.write(f"🏠 **{m['c_s']}**{mostra_rank_c}")
                            st.write(f"📊 Stile (10gg): <span class='{'stile-orizzontale' if 'Orizz' in m['stile_c'] else 'stile-verticale'}'>{m['stile_c']}</span>", unsafe_allow_html=True)
                            st.write(f"⚽ Possesso: {m['poss_c']:.1f}% | 🎯 Tiri Area/match: {m['box_c']:.1f}")
                            st.write(f"🧤 Parate/match: {m['parate_c']:.1f} | 🛑 Falli/match: {m['falli_c']:.1f}")
                            st.write(f"🔪 Cinismo: **1 Gol ogni {m['conv_c']:.1f} tiri in area**")
                            st.write(f"🛡️ Clean Sheet: <span class='cs-testo'>{m['cs_c']:.0f}%</span> | ❌ A secco: <span class='fts-testo'>{m['fts_c']:.0f}%</span>", unsafe_allow_html=True)
                        with col2:
                            mostra_rank_t = "" if camp in ["🇪🇺 Champions League", "🇪🇺 Europa League", "🇪🇺 Conference League"] else f" (Pos: {m['rank_t']}ª)"
                            st.write(f"✈️ **{m['t_s']}**{mostra_rank_t}")
                            st.write(f"📊 Stile (10gg): <span class='{'stile-orizzontale' if 'Orizz' in m['stile_t'] else 'stile-verticale'}'>{m['stile_t']}</span>", unsafe_allow_html=True)
                            st.write(f"⚽ Possesso: {m['poss_t']:.1f}% | 🎯 Tiri Area/match: {m['box_t']:.1f}")
                            st.write(f"🧤 Parate/match: {m['parate_t']:.1f} | 🛑 Falli/match: {m['falli_t']:.1f}")
                            st.write(f"🔪 Cinismo: **1 Gol ogni {m['conv_t']:.1f} tiri in area**")
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
                            st.markdown("<p class='label-bold'>Assenti & V90 Radar</p>", unsafe_allow_html=True)
                            # V90: Icone specifiche per Portiere e Difesa
                            c_star = f" (<span class='star-testo'>{m['t1_c']} Star</span>)" if m['t1_c'] > 0 else ""
                            t_star = f" (<span class='star-testo'>{m['t1_t']} Star</span>)" if m['t1_t'] > 0 else ""
                            sq_c_badge = f" <span class='star-testo'>[{m['sq_c']} 🟥]</span>" if m['sq_c'] > 0 else ""
                            sq_t_badge = f" <span class='star-testo'>[{m['sq_t']} 🟥]</span>" if m['sq_t'] > 0 else ""
                            gk_badge_c = " 🧤🚫" if m['gk_out_c'] else ""
                            gk_badge_t = " 🧤🚫" if m['gk_out_t'] else ""
                            def_badge_c = " 🧱⚠️" if m['def_out_c'] >= 2 else ""
                            def_badge_t = " 🧱⚠️" if m['def_out_t'] >= 2 else ""
                            
                            st.write(f"🏠 🚑 {m['count_c']} Assenti{c_star}{sq_c_badge}{gk_badge_c}{def_badge_c}", unsafe_allow_html=True)
                            st.write(f"✈️ 🚑 {m['count_t']} Assenti{t_star}{sq_t_badge}{gk_badge_t}{def_badge_t}", unsafe_allow_html=True)
                        with c4: 
                            st.markdown("<p class='label-bold'>DNA Storico & Ritardi</p>", unsafe_allow_html=True)
                            st.write(f"<span class='dna-testo'>{m['dna_h2h']}</span>", unsafe_allow_html=True)
                            st.write(f"<span class='ritardo-testo'>Ritardi 🏠: {m['rit_c']} | ✈️: {m['rit_t']}</span>", unsafe_allow_html=True)
                            st.markdown(f"<div class='h2h-details'>{m['dettagli_h2h']}</div>", unsafe_allow_html=True)
                        
                        cc1, cc2, cc3 = st.columns(3)
                        cc1.metric("🚩 Corner / Match", f"{m['corn_tot']:.1f}")
                        cc2.metric("🟨 Cartellini / Match", f"{m['cart_tot']:.1f}")
                        cc3.metric("🛑 Falli Totali / Match", f"{m['falli_tot']:.1f}")

                        if m['best_1x2'][0] == "No Segno Fisso":
                            st.markdown(f"<div class='pure-1x2'>⚠️ <b>NESSUN SEGNO SECCO CONSIGLIATO</b></div>", unsafe_allow_html=True)
                        else:
                            badge_1x2_class = "quota-badge" if m['best_1x2'][3] else "quota-badge-calc"
                            badge_1x2_text = "Ufficiale Bet365" if m['best_1x2'][3] else "Calibrata"
                            st.markdown(f"<div class='pure-1x2'>👑 Miglior Segno Secco: <b>{m['best_1x2'][0]}</b> ({m['best_1x2'][1]:.1f}%) <span class='{badge_1x2_class}'>Quota {badge_1x2_text}: {m['best_1x2'][2]}</span></div>", unsafe_allow_html=True)
                        
                        exclude_safe = ["U4.5", "O0.5", "O1.5", "Casa O0.5", "Ospite O0.5"]
                        filtered_tips = {k: v for k, v in m['all_tips'].items() if k not in exclude_safe}
                        top_3 = sorted(filtered_tips.items(), key=lambda x: x[1], reverse=True)[:3]
                        
                        q1, _ = get_quota_finale(top_3[0][0], top_3[0][1], m['quote_reali'])
                        q2, _ = get_quota_finale(top_3[1][0], top_3[1][1], m['quote_reali'])
                        q3, _ = get_quota_finale(top_3[2][0], top_3[2][1], m['quote_reali'])

                        st.markdown("<div class='top-pick-box'>", unsafe_allow_html=True)
                        st.write("🎯 **TOP 3 ASSOLUTE (Ordinate per Probabilità Pura):**")
                        col_a, col_b, col_c = st.columns(3)
                        col_a.write(f"<span class='gold-medal'>🥇 {top_3[0][0]}</span> ({top_3[0][1]:.1f}%) <span class='quota-badge-calc'>Quota: {q1}</span>", unsafe_allow_html=True)
                        col_b.write(f"<span class='silver-medal'>🥈 {top_3[1][0]}</span> ({top_3[1][1]:.1f}%) <span class='quota-badge-calc'>Quota: {q2}</span>", unsafe_allow_html=True)
                        col_c.write(f"<span class='bronze-medal'>🥉 {top_3[2][0]}</span> ({top_3[2][1]:.1f}%) <span class='quota-badge-calc'>Quota: {q3}</span>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)

    with t3:
        st.header("🏆 Generatore Automatico Ottimizzato (V90)")
        st.write("Motore Giocatori V90 Attivo: Calcola Rating individuali, Danno di Reparto, e Portieri Titolari Assenti.")
        
        budget_safety = budget_totale * 0.60
        budget_perf = budget_totale * 0.30
        budget_azzardo = budget_totale * 0.10
        
        if len(st.session_state.all_tips_global) >= 4:
            testo_export = f"=== MATRIX V90: SCHEDINE AUTOMATICHE ===\nPeriodo: {start_str} / {end_str}\n\n"
            
            st.markdown("<div class='strategy-box safety-bg'>", unsafe_allow_html=True)
            st.subheader("🟢 Schedina SAFETY (Muro di Berlino Attivo)")
            st.markdown(f"<span class='budget-tag'>💰 Puntata Allocata: {budget_safety:.2f}€ (60% del Budget)</span>", unsafe_allow_html=True)
            
            vietati_safety = ["Goal", "O1.5", "O2.5", "O3.5", "O4.5"]
            pool_safety = [x for x in st.session_state.all_tips_global if x['Tip'] not in vietati_safety]
            
            s_slip, q_tot_s, prob_s, usate_safety = costruisci_schedina_dinamica(pool_safety, 1.12, 1.50, target_mult=2.0, max_righe=6, max_same_family=2, escludi_match=set())
            testo_export += f"🟢 SAFETY (Puntata: {budget_safety:.2f}€)\n"
            for x in s_slip:
                bc = "quota-badge" if x['Real'] else "quota-badge-calc"
                st.write(f"• <span class='orario-match'>[{x['Time']}]</span> {x['Match']}: **{x['Tip']}** <span class='{bc}'>Q: {x['Quota']}</span>", unsafe_allow_html=True)
                testo_export += f"- [{x['Time']}] {x['Match']} -> {x['Tip']} @ {x['Quota']:.2f}\n"
            col_s1, col_s2 = st.columns(2)
            col_s1.metric("Vincita Stimata", f"~{budget_safety * q_tot_s:.2f}€")
            col_s2.metric("Probabilità Congiunta", f"{prob_s*100:.2f}%")
            testo_export += f"Totale Quota: {q_tot_s:.2f} | Probabilità: {prob_s*100:.2f}% | Vincita: ~{budget_safety * q_tot_s:.2f}€\n\n"
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='strategy-box performance-bg'>", unsafe_allow_html=True)
            st.subheader("🟠 Schedina PERFORMANCE")
            st.markdown(f"<span class='budget-tag'>💰 Puntata Allocata: {budget_perf:.2f}€ (30% del Budget)</span>", unsafe_allow_html=True)
            p_slip, q_tot_p, prob_p, usate_perf = costruisci_schedina_dinamica(st.session_state.all_tips_global, 1.51, 2.20, target_mult=5.0, max_righe=6, max_same_family=2, escludi_match=usate_safety)
            testo_export += f"🟠 PERFORMANCE (Puntata: {budget_perf:.2f}€)\n"
            for x in p_slip:
                bc = "quota-badge" if x['Real'] else "quota-badge-calc"
                st.write(f"• <span class='orario-match'>[{x['Time']}]</span> {x['Match']}: **{x['Tip']}** <span class='{bc}'>Q: {x['Quota']}</span>", unsafe_allow_html=True)
                testo_export += f"- [{x['Time']}] {x['Match']} -> {x['Tip']} @ {x['Quota']:.2f}\n"
            col_p1, col_p2 = st.columns(2)
            col_p1.metric("Vincita Stimata", f"~{budget_perf * q_tot_p:.2f}€")
            col_p2.metric("Probabilità Congiunta", f"{prob_p*100:.2f}%")
            testo_export += f"Totale Quota: {q_tot_p:.2f} | Probabilità: {prob_p*100:.2f}% | Vincita: ~{budget_perf * q_tot_p:.2f}€\n\n"
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='strategy-box risk-bg'>", unsafe_allow_html=True)
            st.subheader("🔴 Schedina AZZARDO")
            st.markdown(f"<span class='budget-tag'>💰 Puntata Allocata: {budget_azzardo:.2f}€ (10% del Budget)</span>", unsafe_allow_html=True)
            r_slip, q_tot_a, prob_a, _ = costruisci_schedina_dinamica(st.session_state.all_tips_global, 2.21, 4.50, target_mult=30.0, max_match_q=4.50, max_righe=6, max_same_family=2, escludi_match=usate_perf)
            testo_export += f"🔴 AZZARDO (Puntata: {budget_azzardo:.2f}€)\n"
            for x in r_slip:
                bc = "quota-badge" if x['Real'] else "quota-badge-calc"
                st.write(f"• <span class='orario-match'>[{x['Time']}]</span> {x['Match']}: **{x['Tip']}** <span class='{bc}'>Q: {x['Quota']}</span>", unsafe_allow_html=True)
                testo_export += f"- [{x['Time']}] {x['Match']} -> {x['Tip']} @ {x['Quota']:.2f}\n"
            col_a1, col_a2 = st.columns(2)
            col_a1.metric("Vincita Stimata", f"~{budget_azzardo * q_tot_a:.2f}€")
            col_a2.metric("Probabilità Congiunta", f"{prob_a*100:.2f}%")
            testo_export += f"Totale Quota: {q_tot_a:.2f} | Probabilità: {prob_a*100:.2f}% | Vincita: ~{budget_azzardo * q_tot_a:.2f}€\n\n"
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.download_button(
                label="💾 SCARICA TUTTE LE 3 SCHEDINE (TXT)",
                data=testo_export,
                file_name=f"Matrix_V90_Tickets_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain"
            )
