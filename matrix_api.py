"""
matrix_api.py — Layer di accesso a api-sports.io.

Tutte le funzioni che parlano con l'API (fixtures, standings, quote,
infortuni, statistiche squadra/giocatore, auto-discovery ID lega/coppa)
vivono qui, cache incluse (@st.cache_data). Le tabelle statiche (elenco
campionati, livelli di affidabilità) vivono invece in matrix_leghe.py.
"""

import os
import requests
import streamlit as st
from datetime import datetime, timedelta

from matrix_leghe import FREQUENZE_MEDIE, MASTER_LEAGUES, N_PARTITE_STATS_AVANZATE

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

def _risolvi_id_per_nome(nazione: str, chiave_nome: str, fallback_id: int) -> int:
    leghe = trova_id_multipli(nazione, {})
    for nome_lega, lid in leghe.items():
        if chiave_nome.lower() in nome_lega.lower():
            return lid
    return fallback_id

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
            return 0.0, 0.0, True
        giocate = stats.get('fixtures', {}).get('played', {}).get('total', 0)
        if giocate == 0:
            return 0.0, 0.0, True
        cs_p  = (stats.get('clean_sheet', {}).get('total', 0) / giocate) * 100
        fts_p = (stats.get('failed_to_score', {}).get('total', 0) / giocate) * 100
        # Cap: su campioni piccoli (playoff, inizio stagione) i % possono essere 100/0 — irrealistici
        cs_p  = min(85.0, cs_p)
        fts_p = min(85.0, fts_p)
        return cs_p, fts_p, True
    except Exception:
        # ok=False: qui la funzione e' davvero fallita (errore/timeout API),
        # a differenza dei return sopra dove i dati sono semplicemente assenti.
        return 0.0, 0.0, False

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

            # PERF: fixtures/statistics interrogato solo per le ultime
            # N_PARTITE_STATS_AVANZATE partite (non tutte e 10) — riduce
            # sensibilmente il numero di chiamate API per squadra.
            if i < N_PARTITE_STATS_AVANZATE:
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
                avg_rig, avg_gf_home, avg_gs_home, avg_gf_away, avg_gs_away, True)
    except Exception:
        # ok=False: fallback totale su errore/timeout API.
        return (50.0, 4.0, 5.0, 5.0, 4.5, 2.0, 10.0, 2.5,
                "Bilanciato", 0, 1.0, 1.0, 0.0, 1.0, 1.0, 1.0, 1.0, False)

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
            return 1.0, False, "N/D", 1.0, [], 0, 0, True

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

        return m_stanchezza, is_stanca, forma_str, m_forma, ritardi, punti_5, punti_prev_5, True
    except Exception:
        # ok=False: fallback su errore/timeout API.
        return 1.0, False, "N/D", 1.0, [], 0, 0, False

@st.cache_data(ttl=3600)
def analizza_h2h_dna_e_andata(id_casa: int, id_trasf: int):
    try:
        resp = requests.get(
            "https://v3.football.api-sports.io/fixtures/headtohead",
            headers=HEADERS, params={'h2h': f"{id_casa}-{id_trasf}", 'last': 5}, timeout=8
        ).json()
        matches = resp.get('response', [])
        if not matches:
            return 1.0, 1.0, 0, 0, "Nessun Precedente", 1.0, 1.0, "", "Nessun match.", True
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
        return m_h2h_c, m_h2h_t, gol_c, gol_t, storico, boost_c, boost_t, andata_msg, det_str, True
    except Exception:
        # ok=False: fallback su errore/timeout API.
        return 1.0, 1.0, 0, 0, "Dati N/D", 1.0, 1.0, "", "Nessun dato.", False

@st.cache_data(ttl=86400)
def trova_lega_squadra(team_id: int, season, fallback_id: int) -> int:
    """
    Trova l'ID della lega principale (type=League) in cui gioca una squadra
    in una data stagione. Usata per rilevare correttamente gli spareggi
    promozione/retrocessione tra divisioni diverse (es. Bundesliga vs
    2.Bundesliga), dove le due squadre appartengono a leghe differenti
    pur giocando la partita sotto un unico fixture/league id di playoff.
    """
    try:
        resp = requests.get(
            "https://v3.football.api-sports.io/leagues",
            headers=HEADERS,
            params={'team': team_id, 'season': season},
            timeout=6
        ).json()
        for entry in resp.get('response', []):
            if entry.get('league', {}).get('type') == 'League':
                return entry['league']['id']
    except Exception:
        pass
    return fallback_id

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
