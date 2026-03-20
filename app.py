import streamlit as st
import requests
import math
import pandas as pd
from datetime import datetime, timezone, timedelta
import pytz

# ==========================================
# 🎨 UI: TOTAL MATRIX DESIGN (V67.2)
# ==========================================
st.set_page_config(page_title="Matrix Bet V67", page_icon="🎯", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1a1a1a; }
    .stExpander { border: 1px solid #e1e4e8 !important; background-color: #ffffff !important; border-radius: 10px !important; box-shadow: 0 1px 4px rgba(0,0,0,0.03) !important; margin-bottom: 10px !important; }
    .stMetric { background-color: #fcfcfc; border: 1px solid #eee; padding: 12px; border-radius: 10px; }
    h1, h2, h3, p, span, label { color: #1a1a1a !important; font-family: 'Segoe UI', sans-serif; }
    .label-bold { font-weight: 700; color: #444; font-size: 0.85em; text-transform: uppercase; margin-bottom: 5px; display: block; }
    .strategy-box { padding: 20px; border-radius: 15px; margin-bottom: 20px; border: 2px solid #e1e4e8; }
    .safety-bg { background-color: #f0fff4; border-color: #38a169; }
    .performance-bg { background-color: #fffaf0; border-color: #dd6b20; }
    .risk-bg { background-color: #fff5f5; border-color: #e53e3e; }
    .table-container { background: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #eee; margin-bottom: 15px; }
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
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURAZIONE ---
API_KEY_FOOTBALL = 'dc4d6488653c2d9a763290a44eb1613f'
STAGIONE = "2025"

MASTER_LEAGUES = {
    "🇪🇺 Champions League": 2, "🇪🇺 Europa League": 3, "🇪🇺 Conference League": 848,
    "🇮🇹 Serie A": 135, "🇮🇹 Serie B": 136, "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": 39, "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Championship": 40,
    "🇪🇸 La Liga": 140, "🇩🇪 Bundesliga": 78, "🇫🇷 Ligue 1": 61,
    "🇳🇱 Eredivisie": 88, "🇵🇹 Primeira Liga": 94, "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Prem.": 281,
    "🇹🇷 Süper Lig": 203, "🇧🇪 Pro League": 144, "🇬🇷 Super League": 197
}

# ==========================================
# 📡 MODULI API E CALCOLI MATEMATICI
# ==========================================

@st.cache_data(ttl=3600)
def get_active_leagues(start_date, end_date):
    active_ids = set()
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {'x-apisports-key': API_KEY_FOOTBALL}
    delta = end_date - start_date
    days_to_check = min(delta.days + 1, 7) 
    try:
        for i in range(days_to_check):
            d_str = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
            resp = requests.get(url, headers=headers, params={'date': d_str}).json()
            if resp.get('errors'): return MASTER_LEAGUES
            if 'response' in resp: active_ids.update({f['league']['id'] for f in resp['response']})
        return {k: v for k, v in MASTER_LEAGUES.items() if v in active_ids}
    except: return MASTER_LEAGUES

@st.cache_data(ttl=86400) 
def get_player_minutes(player_id, season):
    if not player_id: return 0
    try:
        url = "https://v3.football.api-sports.io/players"
        headers = {'x-apisports-key': API_KEY_FOOTBALL}
        resp = requests.get(url, headers=headers, params={'id': player_id, 'season': season}).json()
        if resp.get('response'):
            stats = resp['response'][0]['statistics']
            return sum(s['games']['minutes'] or 0 for s in stats if s['games']['minutes'])
        return 0
    except: return 0

def analizza_infortuni_pesati(inf_list, partite_giocate_team):
    malus = 0.0; t1_star, t2_rot, t3_ris = 0, 0, 0; visti = set()
    max_mins_possibili = max(1, partite_giocate_team * 90)
    for i in inf_list:
        p_id = i['player'].get('id')
        if not p_id or p_id in visti: continue
        visti.add(p_id)
        ratio = get_player_minutes(p_id, STAGIONE) / max_mins_possibili
        if ratio >= 0.50: malus += 0.15; t1_star += 1
        elif ratio >= 0.20: malus += 0.05; t2_rot += 1
        else: malus += 0.01; t3_ris += 1
    return min(0.40, malus), t1_star, t2_rot, t3_ris, len(visti)

@st.cache_data(ttl=3600)
def scarica_quote_native(league_id, date_str):
    try:
        url = "https://v3.football.api-sports.io/odds"
        headers = {'x-apisports-key': API_KEY_FOOTBALL}
        resp = requests.get(url, headers=headers, params={'league': league_id, 'season': STAGIONE, 'date': date_str, 'bookmaker': 8}).json()
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

def converti_prob_in_quota(prob_percentuale):
    if prob_percentuale <= 0: return 50.0
    if prob_percentuale > 98: return 1.05
    quota_fair = 100 / prob_percentuale
    return max(1.01, round(1.0 + ((quota_fair - 1.0) * 1.55), 2))

def get_quota_finale(tip, prob, quote_reali):
    if quote_reali and tip in quote_reali: return quote_reali[tip], True
    return converti_prob_in_quota(prob), False

@st.cache_data(ttl=3600)
def analizza_squadra_globale(team_id):
    try:
        url = "https://v3.football.api-sports.io/fixtures"
        headers = {'x-apisports-key': API_KEY_FOOTBALL}
        resp = requests.get(url, headers=headers, params={'team': team_id, 'last': 10, 'status': 'FT'}).json()
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
            if gh == ga: stats['D'] += 1
            elif (is_home and gh > ga) or (not is_home and ga > ga): stats['W'] += 1
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
        url = "https://v3.football.api-sports.io/fixtures/headtohead"
        headers = {'x-apisports-key': API_KEY_FOOTBALL}
        resp = requests.get(url, headers=headers, params={'h2h': f"{id_casa}-{id_trasf}", 'last': 5}).json()
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

def calcola_tutti_i_mercati(xg_c, xg_t, tension_index):
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

    # Integrazione Calcoli Cartellini e Angoli (Proxy Alta Fedeltà x 7500 API)
    exp_corners = (xg_c + xg_t) * 4.0 + 1.8 
    exp_cards = tension_index * 4.5
    special = {
        "Over 8.5 Angoli": min(92.0, max(15.0, (exp_corners / 9.5) * 50)),
        "Over 4.5 Cartellini": min(88.0, max(20.0, (exp_cards / 5.0) * 50))
    }

    return {**p, **mg, **re_prob, **combos, **htft, **special}

def semplifica_nome(nome):
    for p in ['FC', 'AC ', ' BC', ' AS', ' Milan', ' Calcio', ' Hotspur', 'AFC ', 'United', 'City', 'SL ']: nome = nome.replace(p, '')
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
        
        # V67.2: Controlliamo che il match non sia mai stato usato né in questa schedina, né nelle altre!
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

st.sidebar.header("⚙️ Centrale Operativa")

date_range = st.sidebar.date_input("Seleziona Periodo (Dal - Al):", [])
if len(date_range) == 2: start_date, end_date = date_range[0], date_range[1]
elif len(date_range) == 1: start_date = end_date = date_range[0]
else: start_date = end_date = datetime.now().date()

start_str = start_date.strftime('%Y-%m-%d')
end_str = end_date.strftime('%Y-%m-%d')

st.sidebar.markdown("---")
budget_totale = st.sidebar.number_input("Budget Totale (€):", min_value=5.0, value=50.0, step=5.0)
st.sidebar.markdown("---")

with st.sidebar.expander("🛠️ Personalizza Schedine", expanded=False):
    st.markdown("🟢 **Range SAFETY**")
    sc1, sc2 = st.columns(2)
    safe_min = sc1.number_input("Min", 1.01, 2.00, 1.30, step=0.01, key="s_min")
    safe_max = sc2.number_input("Max", safe_min, 3.00, 1.50, step=0.01, key="s_max")
    safe_target = st.number_input("Target Raddoppio", 1.5, 10.0, 2.0, step=0.5, key="st")
    
    st.markdown("---")
    st.markdown("🟠 **Range PERFORMANCE**")
    pc1, pc2 = st.columns(2)
    perf_min = pc1.number_input("Min", 1.10, 3.00, 1.51, step=0.01, key="p_min")
    perf_max = pc2.number_input("Max", perf_min, 5.00, 1.80, step=0.01, key="p_max")
    perf_target = st.number_input("Target Moltiplicatore", 2.0, 20.0, 5.0, step=0.5, key="pt")
    
    st.markdown("---")
    st.markdown("🔴 **Range AZZARDO**")
    ac1, ac2 = st.columns(2)
    azz_min = ac1.number_input("Min", 1.30, 5.00, 1.81, step=0.01, key="a_min")
    azz_max = ac2.number_input("Max", azz_min, 20.00, 2.80, step=0.01, key="a_max")
    azz_target = st.number_input("Target Quota Totale", 10.0, 200.0, 30.0, step=5.0, key="at")

st.sidebar.markdown("---")

with st.sidebar:
    if st.button("🔍 Trova Campionati Attivi nel Periodo"):
        with st.spinner("Scansione palinsesto in corso..."):
            st.session_state['active_leagues'] = get_active_leagues(start_date, end_date)

if 'active_leagues' not in st.session_state: st.session_state['active_leagues'] = MASTER_LEAGUES 
active_dict = st.session_state['active_leagues']
if not active_dict: st.sidebar.warning("Nessun campionato supportato attivo.")
scelte = st.sidebar.multiselect("Campionati in campo:", list(active_dict.keys()), default=list(active_dict.keys()))

btn_genera = st.sidebar.button("⚡ ESTRAI MATRIX EUROPEA")

if btn_genera:
    st.session_state.data_master = {}
    st.session_state.all_tips_global = []
    headers = {'x-apisports-key': API_KEY_FOOTBALL}
    now_utc = datetime.now(timezone.utc)
    tz_ita = pytz.timezone('Europe/Rome')
    mese_attuale = datetime.now().month

    for name in scelte:
        f_id = active_dict[name]
        with st.spinner(f"Calcolo Punti e Motivazioni {name}..."):
            fix = requests.get("https://v3.football.api-sports.io/fixtures", headers=headers, params={'league': f_id, 'season': STAGIONE, 'from': start_str, 'to': end_str}).json()
            std = requests.get("https://v3.football.api-sports.io/standings", headers=headers, params={'league': f_id, 'season': STAGIONE}).json()
            
            if not fix.get('response'): continue

            db_stats = {}
            punti_champions, punti_salvezza, tot_squadre, partite_totali_campionato = 0, 0, 20, 38
            if std.get('response') and len(std['response']) > 0 and 'league' in std['response'][0] and 'standings' in std['response'][0]['league']:
                gruppo = std['response'][0]['league']['standings'][0]
                tot_squadre = len(gruppo)
                partite_totali_campionato = (tot_squadre - 1) * 2
                
                if tot_squadre >= 18:
                    punti_champions = gruppo[3]['points'] 
                    punti_salvezza = gruppo[tot_squadre - 4]['points'] 
                
                for t in gruppo:
                    n = semplifica_nome(t['team']['name'])
                    db_stats[n] = {
                        'id': t['team']['id'], 'rank': t['rank'], 
                        'giocate': t['all']['played'], 'punti': t['points'],
                        'ac': t['home']['goals']['for'] / max(1, t['home']['played']),
                        'dc': t['home']['goals']['against'] / max(1, t['home']['played']),
                        'at': t['away']['goals']['for'] / max(1, t['away']['played']),
                        'dt': t['away']['goals']['against'] / max(1, t['away']['played'])
                    }

            matches_list = []
            date_giocate = {f['fixture']['date'][:10] for f in fix['response']}
            inj_cache = {}
            odds_cache = {}
            for d_match in date_giocate:
                inj_cache[d_match] = requests.get("https://v3.football.api-sports.io/injuries", headers=headers, params={'league': f_id, 'season': STAGIONE, 'date': d_match}).json()
                odds_cache[d_match] = scarica_quote_native(f_id, d_match)

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
                if c_s not in db_stats or t_s not in db_stats: continue

                quote_reali_match = odds_cache.get(match_date_str, {}).get(fix_id, {})
                inj = inj_cache.get(match_date_str, {})

                m_st_c, is_stanca_c, forma_c, m_f_c, rit_c = analizza_squadra_globale(db_stats[c_s]['id'])
                m_st_t, is_stanca_t, forma_t, m_f_t, rit_t = analizza_squadra_globale(db_stats[t_s]['id'])
                m_met, d_met = scarica_meteo(c_s)
                
                m_h2h_c, m_h2h_t, gol_h2h_c, gol_h2h_t, str_h2h, b_and_c, b_and_t, andata_msg, dettagli_h2h_str = analizza_h2h_dna_e_andata(db_stats[c_s]['id'], db_stats[t_s]['id'])
                
                inf_all = inj.get('response', [])
                if not isinstance(inf_all, list): inf_all = []
                inf_c_list = [i for i in inf_all if semplifica_nome(i['team']['name']) == c_s]
                inf_t_list = [i for i in inf_all if semplifica_nome(i['team']['name']) == t_s]
                
                malus_c, t1_c, t2_c, t3_c, count_c = analizza_infortuni_pesati(inf_c_list, db_stats[c_s]['giocate'])
                malus_t, t1_t, t2_t, t3_t, count_t = analizza_infortuni_pesati(inf_t_list, db_stats[t_s]['giocate'])
                
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

                    # Analisi CASA (V67.1 Corretta)
                    if rank_c <= 6 or (punti_champions - punti_c) <= 7 and (punti_champions - punti_c) > 0:
                        m_mot_c = 1.15; msg_mot += "🏆 C. Vertice "
                    elif rank_c >= tot_squadre - 6:
                        m_mot_c = 1.20; msg_mot += "🆘 C. Disperata "
                        tension_idx += 0.15
                    elif mese_attuale >= 3 and (punti_c - punti_salvezza) > 9 and (punti_champions - punti_c) > 10:
                        m_mot_c = 1.10; msg_mot += "🌴 C. Sgombra "
                    else:
                        m_mot_c = 1.05
                    
                    # Analisi OSPITE (V67.1 Corretta)
                    if rank_t <= 6 or (punti_champions - punti_t) <= 7 and (punti_champions - punti_t) > 0:
                        m_mot_t = 1.15; msg_mot += "🏆 O. Vertice"
                    elif rank_t >= tot_squadre - 6:
                        m_mot_t = 1.20; msg_mot += "🆘 O. Disperata"
                        tension_idx += 0.15
                    elif mese_attuale >= 3 and (punti_t - punti_salvezza) > 9 and (punti_champions - punti_t) > 10:
                        m_mot_t = 1.10; msg_mot += "🌴 O. Sgombra"
                    else:
                        m_mot_t = 1.05

                    if abs(rank_c - rank_t) <= 3: tension_idx += 0.2

                xg_base_c = math.sqrt(max(0.01, db_stats[c_s]['ac']) * max(0.01, db_stats[t_s]['dt'])) * m_f_c * m_st_c
                xg_base_t = math.sqrt(max(0.01, db_stats[t_s]['at']) * max(0.01, db_stats[c_s]['dc'])) * m_f_t * m_st_t
                
                se_sgombra_c = "C. Sgombra" in msg_mot
                se_sgombra_t = "O. Sgombra" in msg_mot
                
                xg_c = xg_base_c * (1 - malus_c) * (1 + (malus_t * 0.5)) * m_h2h_c * b_and_c * m_mot_c * (1.10 if se_sgombra_t else 1.0)
                xg_t = xg_base_t * (1 - malus_t) * (1 + (malus_c * 0.5)) * m_h2h_t * b_and_t * m_mot_t * (1.10 if se_sgombra_c else 1.0)
                
                msg_streak = ""
                if streak_breaker_c: xg_c = max(1.15, xg_c * 1.45); msg_streak += "🔥 STREAK CASA "
                if streak_breaker_t: xg_t = max(1.15, xg_t * 1.45); msg_streak += "🔥 STREAK OSPITE"
                
                xg_c *= m_met; xg_t *= m_met
                
                arb = f['fixture']['referee'] or "N/D"
                is_sev = any(s in str(arb) for s in ["Orsato", "Maresca", "Taylor", "Oliver", "Lahoz", "Hernandez"])
                m_arb = 1.05 if is_sev else 1.0
                xg_c *= m_arb; xg_t *= m_arb
                if is_sev: tension_idx += 0.4

                full_tips = calcola_tutti_i_mercati(xg_c, xg_t, tension_idx)
                
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
                    "all_tips": full_tips, "best_1x2": (best_1x2_key, best_1x2_prob, best_1x2_q, best_1x2_real),
                    "quote_reali": quote_reali_match,
                    "xg_c": xg_c, "xg_t": xg_t, "arb": arb, "is_sev": is_sev,
                    "count_c": count_c, "t1_c": t1_c, "t2_c": t2_c, "t3_c": t3_c,
                    "count_t": count_t, "t1_t": t1_t, "t2_t": t2_t, "t3_t": t3_t,
                    "meteo": d_met, "dna_h2h": str_h2h, "dettagli_h2h": dettagli_h2h_str, "streak_msg": msg_streak.strip(), "andata_msg": andata_msg, "msg_mot": msg_mot.strip(),
                    "stan_c": "⚠️ Fatigue" if is_stanca_c else "✅ Riposo", 
                    "stan_t": "⚠️ Fatigue" if is_stanca_t else "✅ Riposo", 
                    "forma_c": forma_c, "forma_t": forma_t, "rit_c": rit_c, "rit_t": rit_t,
                })
            if matches_list: st.session_state.data_master[name] = matches_list

# --- DISPLAY DELLE TAB COMPLETAMENTE RIPRISTINATO ---
if st.session_state.data_master:
    t1, t2, t3 = st.tabs(["🌟 CLASSIFICHE OMNI-MARKET", "🔬 ESPLORATORE PARTITE", "🏆 SCHEDINE VALUE DINAMICHE"])
    
    with t1:
        st.header("👑 Top 10 Assoluta d'Europa (Probabilità Pura)")
        pool_absolute = [x for x in st.session_state.all_tips_global if x['Tip'] not in ["U4.5", "Casa O0.5", "Ospite O0.5"]]
        df_all = pd.DataFrame(pool_absolute)
        if not df_all.empty:
            st.dataframe(df_all[['Time', 'Match', 'League', 'Tip', 'Prob', 'Quota']].sort_values(by="Prob", ascending=False).head(10).style.format({"Prob": "{:.1f}%", "Quota": "{:.2f}"}), hide_index=True, use_container_width=True)

        st.write("---")
        st.header("📊 Top 10 per Categorie Esclusive")
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("<div class='table-container'>", unsafe_allow_html=True)
            st.subheader("🧬 Migliori Combo (1X2 + U/O)")
            pool_combo = [x for x in st.session_state.all_tips_global if "+" in x['Tip']]
            if pool_combo: st.dataframe(pd.DataFrame(pool_combo).sort_values(by="Prob", ascending=False).head(10)[['Match', 'Tip', 'Prob', 'Quota']].style.format({"Prob": "{:.1f}%", "Quota": "{:.2f}"}), hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col_c2:
            st.markdown("<div class='table-container'>", unsafe_allow_html=True)
            st.subheader("⚽ Mercati Multigol")
            pool_mg = [x for x in st.session_state.all_tips_global if "MG " in x['Tip']]
            if pool_mg: st.dataframe(pd.DataFrame(pool_mg).sort_values(by="Prob", ascending=False).head(10)[['Match', 'Tip', 'Prob', 'Quota']].style.format({"Prob": "{:.1f}%", "Quota": "{:.2f}"}), hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("<div class='table-container'>", unsafe_allow_html=True)
            st.subheader("🎯 Risultati Esatti & HT/FT")
            pool_re = [x for x in st.session_state.all_tips_global if "Risultato" in x['Tip'] or "HT/FT" in x['Tip']]
            if pool_re: st.dataframe(pd.DataFrame(pool_re).sort_values(by="Prob", ascending=False).head(10)[['Match', 'Tip', 'Prob', 'Quota']].style.format({"Prob": "{:.1f}%", "Quota": "{:.2f}"}), hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with col2:
            st.markdown("<div class='table-container'>", unsafe_allow_html=True)
            st.subheader("⚖️ Pari / Dispari")
            pool_pd = [x for x in st.session_state.all_tips_global if x['Tip'] in ["Pari", "Dispari"]]
            if pool_pd: st.dataframe(pd.DataFrame(pool_pd).sort_values(by="Prob", ascending=False).head(10)[['Match', 'Tip', 'Prob', 'Quota']].style.format({"Prob": "{:.1f}%", "Quota": "{:.2f}"}), hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)

        col3, col4 = st.columns(2)
        with col3:
            st.markdown("<div class='table-container'>", unsafe_allow_html=True)
            st.subheader("🛡️ Doppie Chance (1X, X2, 12)")
            pool_dc = [x for x in st.session_state.all_tips_global if x['Tip'] in ["1X", "X2", "12"]]
            if pool_dc: st.dataframe(pd.DataFrame(pool_dc).sort_values(by="Prob", ascending=False).head(10)[['Match', 'Tip', 'Prob', 'Quota']].style.format({"Prob": "{:.1f}%", "Quota": "{:.2f}"}), hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with col4:
            st.markdown("<div class='table-container'>", unsafe_allow_html=True)
            st.subheader("Under / Over & Goal")
            pool_uo = [x for x in st.session_state.all_tips_global if x['Tip'] in ["U1.5", "O1.5", "U2.5", "O2.5", "U3.5", "Goal", "NoGoal", "Over 8.5 Angoli", "Over 4.5 Cartellini"]]
            if pool_uo: st.dataframe(pd.DataFrame(pool_uo).sort_values(by="Prob", ascending=False).head(10)[['Match', 'Tip', 'Prob', 'Quota']].style.format({"Prob": "{:.1f}%", "Quota": "{:.2f}"}), hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with t2:
        st.write(f"Partite UFFICIALI V67.2 per il periodo **{start_str} / {end_str}**.")
        for camp, matches in st.session_state.data_master.items():
            with st.expander(f"🏆 {camp}", expanded=False):
                matches = sorted(matches, key=lambda x: x['orario'])
                for m in matches:
                    with st.expander(f"🕒 {m['orario']} | 🏟️ {m['c_u']} vs {m['t_u']}", expanded=False):
                        st.write(f"**Arbitro:** {m['arb']} | **VAR:** {'⚠️ Impatto Alto' if m['is_sev'] else '✅ Standard'} | **Clima:** {m['meteo']}")
                        
                        if m['msg_mot']: st.write(f"<span class='mot-testo'>{m['msg_mot']}</span>", unsafe_allow_html=True)
                        if m['andata_msg']: st.write(f"<span class='andata-testo'>{m['andata_msg']}</span>", unsafe_allow_html=True)
                        if m['streak_msg']: st.write(f"<span class='streak-testo'>{m['streak_msg']}</span>", unsafe_allow_html=True)

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
                            st.markdown("<p class='label-bold'>Infortuni & Assenti</p>", unsafe_allow_html=True)
                            c_star = f" (<span class='star-testo'>{m['t1_c']} Star</span>)" if m['t1_c'] > 0 else ""
                            t_star = f" (<span class='star-testo'>{m['t1_t']} Star</span>)" if m['t1_t'] > 0 else ""
                            st.write(f"🏠 🚑 {m['count_c']} Assenti{c_star}", unsafe_allow_html=True)
                            st.write(f"✈️ 🚑 {m['count_t']} Assenti{t_star}", unsafe_allow_html=True)
                        with c4: 
                            st.markdown("<p class='label-bold'>DNA Storico & Ritardi</p>", unsafe_allow_html=True)
                            st.write(f"<span class='dna-testo'>{m['dna_h2h']}</span>", unsafe_allow_html=True)
                            st.write(f"<span class='ritardo-testo'>Ritardi 🏠: {m['rit_c']} | ✈️: {m['rit_t']}</span>", unsafe_allow_html=True)
                            st.markdown(f"<div class='h2h-details'>{m['dettagli_h2h']}</div>", unsafe_allow_html=True)
                        
                        if m['best_1x2'][0] == "No Segno Fisso":
                            st.markdown(f"<div class='pure-1x2'>⚠️ <b>NESSUN SEGNO SECCO CONSIGLIATO</b>: Match troppo in equilibrio per l'1X2. Affidarsi ai mercati Goal o U/O.</div>", unsafe_allow_html=True)
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
        st.header("🏆 Generatore Ripartizione Budget Dinamico")
        budget_safety = budget_totale * 0.60
        budget_perf = budget_totale * 0.30
        budget_azzardo = budget_totale * 0.10
        
        testo_export = f"=== MATRIX V67.2: SCHEDINE ===\nPeriodo: {start_str} / {end_str}\n\n"
        
        if len(st.session_state.all_tips_global) >= 4:
            st.markdown("<div class='strategy-box safety-bg'>", unsafe_allow_html=True)
            st.subheader(f"🟢 Schedina SAFETY (Fascia {safe_min} - {safe_max}) | Puntata: {budget_safety:.2f}€")
            s_slip, q_tot_s, prob_s, usate_safety = costruisci_schedina_dinamica(st.session_state.all_tips_global, safe_min, safe_max, target_mult=safe_target, max_righe=6, max_same_family=2, escludi_match=set())
            
            testo_export += f"🟢 SAFETY ({budget_safety:.2f}€) - {len(s_slip)} Eventi\n"
            for x in s_slip:
                badge_class = "quota-badge" if x['Real'] else "quota-badge-calc"
                st.write(f"• <span class='orario-match'>[{x['Time']}]</span> {x['Match']}: **{x['Tip']}** <span class='{badge_class}'>Quota: {x['Quota']}</span>", unsafe_allow_html=True)
                testo_export += f"[{x['Time']}] {x['Match']} -> {x['Tip']} (Q: {x['Quota']})\n"
            st.write("---")
            col_s1, col_s2 = st.columns(2)
            col_s1.metric("Vincita Stimata", f"~{budget_safety * q_tot_s:.2f}€")
            col_s2.metric("Probabilità Congiunta", f"{prob_s*100:.2f}%")
            st.markdown("</div>", unsafe_allow_html=True)
            testo_export += f"Vincita: {budget_safety * q_tot_s:.2f}€\n\n"

            st.markdown("<div class='strategy-box performance-bg'>", unsafe_allow_html=True)
            st.subheader(f"🟠 Schedina PERFORMANCE (Fascia {perf_min} - {perf_max}) | Puntata: {budget_perf:.2f}€")
            p_slip, q_tot_p, prob_p, usate_perf = costruisci_schedina_dinamica(st.session_state.all_tips_global, perf_min, perf_max, target_mult=perf_target, max_righe=6, max_same_family=2, escludi_match=usate_safety)
            
            testo_export += f"🟠 PERFORMANCE ({budget_perf:.2f}€) - {len(p_slip)} Eventi\n"
            for x in p_slip:
                badge_class = "quota-badge" if x['Real'] else "quota-badge-calc"
                st.write(f"• <span class='orario-match'>[{x['Time']}]</span> {x['Match']}: **{x['Tip']}** <span class='{badge_class}'>Quota: {x['Quota']}</span>", unsafe_allow_html=True)
                testo_export += f"[{x['Time']}] {x['Match']} -> {x['Tip']} (Q: {x['Quota']})\n"
            st.write("---")
            col_p1, col_p2 = st.columns(2)
            col_p1.metric("Vincita Stimata", f"~{budget_perf * q_tot_p:.2f}€")
            col_p2.metric("Probabilità Congiunta", f"{prob_p*100:.2f}%")
            st.markdown("</div>", unsafe_allow_html=True)
            testo_export += f"Vincita: {budget_perf * q_tot_p:.2f}€\n\n"

            st.markdown("<div class='strategy-box risk-bg'>", unsafe_allow_html=True)
            st.subheader(f"🔴 Schedina AZZARDO (Fascia {azz_min} - {azz_max}) | Puntata: {budget_azzardo:.2f}€")
            r_slip, q_tot_a, prob_a, _ = costruisci_schedina_dinamica(st.session_state.all_tips_global, azz_min, azz_max, target_mult=azz_target, max_match_q=azz_max, max_righe=6, max_same_family=2, escludi_match=usate_perf)
            
            testo_export += f"🔴 AZZARDO ({budget_azzardo:.2f}€) - {len(r_slip)} Eventi\n"
            for x in r_slip:
                badge_class = "quota-badge" if x['Real'] else "quota-badge-calc"
                st.write(f"• <span class='orario-match'>[{x['Time']}]</span> {x['Match']}: **{x['Tip']}** <span class='{badge_class}'>Quota: {x['Quota']}</span>", unsafe_allow_html=True)
                testo_export += f"[{x['Time']}] {x['Match']} -> {x['Tip']} (Q: {x['Quota']})\n"
            st.write("---")
            col_a1, col_a2 = st.columns(2)
            col_a1.metric("Vincita Stimata", f"~{budget_azzardo * q_tot_a:.2f}€")
            col_a2.metric("Probabilità Congiunta", f"{prob_a*100:.2f}%")
            st.markdown("</div>", unsafe_allow_html=True)
            testo_export += f"Vincita: {budget_azzardo * q_tot_a:.2f}€\n"
            
            st.download_button(label="📥 Scarica Schedine per WhatsApp", data=testo_export, file_name="matrix_schedine.txt", mime="text/plain")
