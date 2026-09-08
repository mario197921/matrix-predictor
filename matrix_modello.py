"""
matrix_modello.py — Motore di calcolo puro: Poisson/xG, quote, edge,
Kelly, generazione schedine. Nessuna funzione qui fa I/O (nessuna
chiamata di rete, nessun uso di streamlit) — sono tutte testabili in
isolamento con semplici assert su input/output.
"""

import itertools
import math
from datetime import datetime, timezone

from matrix_leghe import MARGINE_BK

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

def get_quota_finale(tip: str, prob: float, quote_reali: dict):
    """FIX: margine realistico 7% invece di 1.55x arbitrario."""
    if quote_reali and tip in quote_reali:
        return quote_reali[tip], True
    if prob <= 0:
        return 99.0, False
    return max(1.01, round((100.0 / prob) * MARGINE_BK, 2)), False

def calcola_edge_pct(prob: float, quota: float) -> float:
    return ((prob / 100.0) * quota - 1.0) * 100.0

def devig_1x2(quote_reali: dict):
    """Toglie il margine del bookmaker dalle quote reali 1/X/2 e restituisce
    le probabilita' "eque" implicite dal mercato (sommano a 100). Ritorna
    None se non sono disponibili tutte e tre le quote reali (es. mercato
    non coperto per quella partita) — in quel caso non si puo' devigare
    correttamente e non va usato come prior."""
    if not quote_reali or not all(k in quote_reali for k in ("1", "X", "2")):
        return None
    grezze = {k: 1.0 / float(quote_reali[k]) for k in ("1", "X", "2") if float(quote_reali[k]) > 0}
    if len(grezze) != 3:
        return None
    tot = sum(grezze.values())
    if tot <= 0:
        return None
    return {k: (v / tot) * 100.0 for k, v in grezze.items()}

def blend_prob_mercato(prob_modello: float, prob_mercato: float, peso_mercato: float) -> float:
    """Media pesata fra la probabilita' del modello e quella implicita dal
    mercato (devigata). peso_mercato in [0,1]: 0 = fidati solo del modello,
    1 = fidati solo del mercato. Usata per correggere le stime nei contesti
    "instabili" (inizio stagione, coppe) dove il modello ha pochi dati e
    puo' discostarsi molto dal mercato senza una vera ragione."""
    peso_mercato = max(0.0, min(1.0, peso_mercato))
    return prob_modello * (1.0 - peso_mercato) + prob_mercato * peso_mercato

def applica_blend_mercato_1x2(full_tips: dict, quote_reali: dict, peso_mercato: float) -> dict:
    """Mescola le probabilita' 1/X/2 del modello con quelle devigate dal
    mercato reale (vedi blend_prob_mercato) e RICALCOLA tutti i mercati
    derivati da 1/X/2 (doppie chance, combo con Over/Under, HT/FT) così da
    restituire un dizionario internamente coerente — senza questo, i mercati
    derivati resterebbero calcolati sulle probabilità pre-blend. Se le
    quote reali 1X2 non sono disponibili (devig_1x2 restituisce None),
    restituisce full_tips invariato."""
    prob_mercato = devig_1x2(quote_reali)
    if prob_mercato is None:
        return full_tips
    p = dict(full_tips)
    for k in ("1", "X", "2"):
        p[k] = blend_prob_mercato(p[k], prob_mercato[k], peso_mercato)

    p["1X"] = p["1"] + p["X"]
    p["X2"] = p["X"] + p["2"]
    p["12"] = p["1"] + p["2"]

    if "O1.5" in p:
        p["1X + Over 1.5"]  = (p["1X"] / 100) * (p["O1.5"] / 100) * 100 * 0.92
        p["X2 + Over 1.5"]  = (p["X2"] / 100) * (p["O1.5"] / 100) * 100 * 0.92
    if "U3.5" in p:
        p["1X + Under 3.5"] = (p["1X"] / 100) * (p["U3.5"] / 100) * 100 * 0.95
        p["X2 + Under 3.5"] = (p["X2"] / 100) * (p["U3.5"] / 100) * 100 * 0.95
    if "O2.5" in p:
        p["1 + Over 2.5"]   = (p["1"]  / 100) * (p["O2.5"] / 100) * 100 * 0.90
        p["2 + Over 2.5"]   = (p["2"]  / 100) * (p["O2.5"] / 100) * 100 * 0.90

    ht_raw  = {"1": p["1"] * 0.9, "X": p["X"] * 1.5, "2": p["2"] * 0.9}
    tot_ht  = sum(ht_raw.values())
    if tot_ht > 0:
        ht_prob = {k: v / tot_ht for k, v in ht_raw.items()}
        for ht in ("1", "X", "2"):
            for ft in ("1", "X", "2"):
                p[f"HT/FT {ht}/{ft}"] = ht_prob[ht] * (p[ft] / 100.0) * 100.0

    return p

def kelly_fraction(prob: float, quota: float, fraz: float = 0.08) -> float:
    p = prob / 100.0; b = quota - 1.0
    if b <= 0: return 0.0
    return max(0.0, ((b * p - (1 - p)) / b) * fraz)

def semplifica_nome(nome: str) -> str:
    """FIX: sostituzione conservativa — evita di troncare nomi come FCB."""
    for token in [' FC', ' AC', ' BC', ' AS', ' Calcio', ' AFC', ' SL']:
        nome = nome.replace(token, '')
    for token in ['FC ', 'AC ', 'AS ', 'AFC ', 'SL ']:
        if nome.startswith(token):
            nome = nome[len(token):]
    return nome.strip()

def blend_prior_stagione(valore_corrente: float, valore_precedente,
                          giocate: int, soglia_partite: int = 10) -> float:
    """Sfuma un valore (es. media gol casa/trasferta) della stagione
    corrente con quello della stagione precedente, quando quest'ultimo e'
    disponibile. A 'giocate' (partite gia' giocate in stagione corrente)
    uguale a 0, ci si affida quasi del tutto alla stagione precedente; da
    'soglia_partite' partite in su, ci si affida solo alla corrente. Se
    valore_precedente e' None (dato non disponibile, es. neopromossa),
    ritorna semplicemente il valore corrente invariato."""
    if valore_precedente is None:
        return valore_corrente
    peso_precedente = max(0.0, 1.0 - (giocate / soglia_partite))
    return valore_corrente * (1.0 - peso_precedente) + valore_precedente * peso_precedente

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
                                  max_same_family: int = 2, max_instabili: int = 1,
                                  ordina_per: str = "edge",
                                  min_prob_congiunta: float = None,
                                  max_prob_congiunta: float = None,
                                  max_quota_finale: float = None):
    """max_instabili: numero massimo di selezioni "instabili" (coppe/playoff/
    inter-lega/squadre con poche partite giocate — vedi flag 'Instabile' in
    app.py) che possono finire nella STESSA schedina combo. In una multipla
    basta che una gamba salti per perdere tutto, quindi concentrare più
    selezioni a dato rumoroso nella stessa giocata somma il rischio invece
    di diversificarlo. Le voci senza il flag (es. nei test) sono trattate
    come stabili di default.

    ordina_per: "edge" (default) sceglie le gambe a edge più alto — massimizza
    il valore atteso dichiarato. "prob" sceglie le gambe a probabilità più
    alta — utile per una schedina "safety" dove l'obiettivo è massimizzare
    la probabilità congiunta. "prob_range" cerca fra tutte le combinazioni
    possibili di max_righe gambe quella con l'edge combinato più alto TRA
    QUELLE la cui probabilità congiunta rientra in
    [min_prob_congiunta, max_prob_congiunta] — un compromesso fra le due:
    resta dentro una fascia di sicurezza scelta, ma dentro quella fascia
    massimizza comunque il valore, invece di ignorarlo del tutto.

    max_quota_finale: tetto massimo (opzionale) alla quota totale combinata.
    Senza questo tetto, il ciclo aggiunge gambe finché q_tot >= target_mult
    e SOLO A QUEL PUNTO si ferma: essendo un prodotto, l'ultima gamba
    aggiunta può far sballare il totale ben oltre target_mult (es. da 25 a
    101 con una sola gamba a quota 4). Se impostato, una gamba candidata
    che farebbe superare questo tetto viene scartata (si prova la prossima
    in ordine di edge/prob) invece di essere comunque aggiunta -- cosi' la
    quota totale finale resta sotto controllo invece di poter esplodere."""
    if escludi_match is None: escludi_match = set()

    if ordina_per == "prob_range":
        lo = 0.0 if min_prob_congiunta is None else min_prob_congiunta
        hi = 1.0 if max_prob_congiunta is None else max_prob_congiunta
        valid_pr = [x for x in pool
                    if min_q <= float(x['Quota']) <= max_q
                    and float(x['Quota']) <= max_match_q
                    and float(x.get('Edge', 0)) > 0
                    and x['Match'] not in escludi_match]
        # limita la combinatoria alle migliori candidate per edge (bastano
        # poche decine di partite al giorno per questa fascia di quota)
        candidati = sorted(valid_pr, key=lambda x: calcola_edge_pct(x['Prob'], float(x['Quota'])),
                            reverse=True)[:30]
        if len(candidati) < max_righe:
            return [], 1.0, 1.0, set(escludi_match)   # non abbastanza candidate per una combo completa
        miglior_combo = None; miglior_edge_tot = None
        for combo in itertools.combinations(candidati, max_righe):
            nomi = [c['Match'] for c in combo]
            if len(set(nomi)) != len(nomi):
                continue   # stessa partita due volte nella combo
            fam_cnt = {}
            supera_family = False
            for c in combo:
                fam = get_family(c['Tip'])
                fam_cnt[fam] = fam_cnt.get(fam, 0) + 1
                if fam_cnt[fam] > max_same_family:
                    supera_family = True; break
            if supera_family:
                continue
            if sum(1 for c in combo if c.get('Instabile', False)) > max_instabili:
                continue
            prob_j = 1.0; edge_tot = 0.0
            for c in combo:
                prob_j    *= c['Prob'] / 100.0
                edge_tot  += calcola_edge_pct(c['Prob'], float(c['Quota']))
            if lo <= prob_j <= hi and (miglior_edge_tot is None or edge_tot > miglior_edge_tot):
                miglior_edge_tot = edge_tot; miglior_combo = combo
        if miglior_combo is None:
            return [], 1.0, 1.0, set(escludi_match)
        sel = list(miglior_combo)
        q_tot = prob_tot = 1.0
        for c in sel:
            q_tot *= float(c['Quota']); prob_tot *= c['Prob'] / 100.0
        usati = {c['Match'] for c in sel}
        return sel, q_tot, prob_tot, usati.union(escludi_match)

    valid = [x for x in pool
             if min_q <= float(x['Quota']) <= max_q
             and float(x['Quota']) <= max_match_q
             and float(x.get('Edge', 0)) > 0]   # solo scommesse con edge positivo reale
    if ordina_per == "prob":
        pool_ord = sorted(valid, key=lambda x: float(x['Prob']), reverse=True)
    else:
        pool_ord = sorted(valid, key=lambda x: calcola_edge_pct(x['Prob'], float(x['Quota'])), reverse=True)
    sel = []; viste = set(); fam_cnt = {}; q_tot = prob_tot = 1.0; instabili_cnt = 0
    for item in pool_ord:
        fam  = get_family(item['Tip'])
        nome = item['Match']
        instabile = bool(item.get('Instabile', False))
        if (nome not in viste and nome not in escludi_match
                and fam_cnt.get(fam, 0) < max_same_family
                and (not instabile or instabili_cnt < max_instabili)):
            # Se aggiungere questa gamba sfonda il tetto massimo e abbiamo
            # gia' almeno una selezione, la scartiamo e proviamo la
            # prossima candidata invece di accettare lo sforamento.
            if (max_quota_finale is not None and sel
                    and q_tot * float(item['Quota']) > max_quota_finale):
                continue
            sel.append(item); viste.add(nome)
            fam_cnt[fam] = fam_cnt.get(fam, 0) + 1
            if instabile: instabili_cnt += 1
            q_tot    *= float(item['Quota'])
            prob_tot *= item['Prob'] / 100.0
        if q_tot >= target_mult or len(sel) >= max_righe: break
    return sel, q_tot, prob_tot, viste.union(escludi_match)


# ── Tracking calibrazione (Firebase) ────────────────────────────────────────

def costruisci_record_schedina(nome: str, data_str: str, selezioni: list,
                                q_tot: float, prob_tot: float, budget: float,
                                creato_il: str = None) -> dict:
    """Funzione pura: prepara il dizionario da salvare su Firestore per una
    schedina generata dall'app. Nessuna chiamata di rete qui -- separata da
    matrix_db.py per essere testabile senza credenziali Firebase.

    'creato_il' e' opzionale (default: timestamp UTC corrente) per permettere
    ai test di passare un valore fisso e avere risultati deterministici.
    """
    if creato_il is None:
        creato_il = datetime.now(timezone.utc).isoformat()
    return {
        "nome": nome,
        "data": data_str,
        "creato_il": creato_il,
        "quota_totale": round(float(q_tot), 4),
        "probabilita_congiunta": round(float(prob_tot), 4),
        "budget": round(float(budget), 2),
        "selezioni": [
            {
                "match": s["Match"],
                "tip": s["Tip"],
                "prob_dichiarata": round(float(s["Prob"]), 2),
                "quota": round(float(s["Quota"]), 2),
                "edge": round(float(s.get("Edge", 0)), 2),
                "league": s.get("League", ""),
                "fixture_id": s.get("FixtureID"),
            }
            for s in selezioni
        ],
        "esito": "in_attesa",   # in_attesa | vinta | persa -- aggiornato dopo le partite
    }


# ── Valutazione esiti reali (per il controllo automatico dei risultati) ────

def _segno_1x2(gol_c: int, gol_t: int) -> str:
    if gol_c > gol_t: return "1"
    if gol_c == gol_t: return "X"
    return "2"


def _mappa_parte_combo(parte: str) -> str:
    """Converte il pezzo di un mercato combo (es. 'Over 1.5') nel formato
    Tip standard (es. 'O1.5') usato altrove nel modello."""
    if parte.startswith("Over "):
        return "O" + parte[len("Over "):]
    if parte.startswith("Under "):
        return "U" + parte[len("Under "):]
    return parte   # "1X", "X2", "1", "2", "Goal", ... gia' nel formato giusto


def valuta_esito_tip(tip: str, gol_c_ft: int, gol_t_ft: int,
                      gol_c_ht: int = None, gol_t_ht: int = None):
    """Valuta se una selezione ('Tip') ha vinto dato il risultato reale
    della partita. Ritorna True (vinta), False (persa), oppure None se il
    mercato non e' automaticamente valutabile con i dati disponibili (es.
    Angoli/Cartellini, che servono statistiche extra non presenti nel
    risultato base; oppure HT/FT senza il punteggio del primo tempo).

    Funzione pura: nessuna chiamata di rete, solo logica sui punteggi.
    """
    tot_ft = gol_c_ft + gol_t_ft

    if tip == "1": return gol_c_ft > gol_t_ft
    if tip == "X": return gol_c_ft == gol_t_ft
    if tip == "2": return gol_c_ft < gol_t_ft
    if tip == "1X": return gol_c_ft >= gol_t_ft
    if tip == "X2": return gol_c_ft <= gol_t_ft
    if tip == "12": return gol_c_ft != gol_t_ft

    if tip == "Goal":   return gol_c_ft > 0 and gol_t_ft > 0
    if tip == "NoGoal": return not (gol_c_ft > 0 and gol_t_ft > 0)

    if tip == "Pari":    return tot_ft % 2 == 0
    if tip == "Dispari": return tot_ft % 2 != 0

    if tip == "Casa O0.5":   return gol_c_ft > 0
    if tip == "Ospite O0.5": return gol_t_ft > 0

    if len(tip) > 1 and tip[0] in ("O", "U") and tip[1:].replace(".", "", 1).isdigit():
        linea = float(tip[1:])
        return tot_ft > linea if tip[0] == "O" else tot_ft < linea

    if tip.startswith("MG "):
        lo_s, hi_s = tip[len("MG "):].split("-")
        return int(lo_s) <= tot_ft <= int(hi_s)

    if tip.startswith("Risultato "):
        gc_s, gt_s = tip[len("Risultato "):].split("-")
        return gol_c_ft == int(gc_s) and gol_t_ft == int(gt_s)

    if tip.startswith("HT/FT "):
        if gol_c_ht is None or gol_t_ht is None:
            return None   # punteggio primo tempo non disponibile
        ht_s, ft_s = tip[len("HT/FT "):].split("/")
        return (_segno_1x2(gol_c_ht, gol_t_ht) == ht_s
                and _segno_1x2(gol_c_ft, gol_t_ft) == ft_s)

    if " + " in tip:
        parti = [_mappa_parte_combo(p) for p in tip.split(" + ")]
        esiti = [valuta_esito_tip(p, gol_c_ft, gol_t_ft, gol_c_ht, gol_t_ht) for p in parti]
        if any(e is None for e in esiti):
            return None
        return all(esiti)

    return None   # mercato non riconosciuto/non valutabile automaticamente


# -- Report analitico aggregato (per uso "silenzioso": nessuna UI pensata ----
# per essere letta a occhio, serve a dare a chi valuta la strategia (umano o
# assistente) tutti i numeri gia' incrociati, senza dover ragionare a mano
# sulle centinaia di gambe salvate) ------------------------------------------
FASCE_QUOTA = [
    (0.0, 1.30, "< 1.30"),
    (1.30, 1.50, "1.30 - 1.49"),
    (1.50, 2.00, "1.50 - 1.99"),
    (2.00, 3.00, "2.00 - 2.99"),
    (3.00, 5.00, "3.00 - 4.99"),
    (5.00, float("inf"), "5.00+"),
]


def _fascia_quota(q: float) -> str:
    for lo, hi, nome in FASCE_QUOTA:
        if lo <= q < hi:
            return nome
    return FASCE_QUOTA[-1][2]


def _nuova_stat():
    return {"vinte": 0, "perse": 0, "attesa": 0, "_quota_sum": 0.0, "_quota_n": 0}


def _registra_gamba(stat: dict, esito_gamba, quota) -> None:
    if esito_gamba == "vinta":
        stat["vinte"] += 1
    elif esito_gamba == "persa":
        stat["perse"] += 1
    else:
        stat["attesa"] += 1
        return
    if quota:
        stat["_quota_sum"] += float(quota)
        stat["_quota_n"] += 1


def _finalizza_stat(stat: dict) -> dict:
    concluse = stat["vinte"] + stat["perse"]
    win_rate = round(stat["vinte"] / concluse * 100, 1) if concluse else None
    quota_media = round(stat["_quota_sum"] / stat["_quota_n"], 3) if stat["_quota_n"] else None
    prob_implicita = round(100.0 / quota_media, 1) if quota_media else None
    edge_vs_implicita = round(win_rate - prob_implicita, 1) if (win_rate is not None and prob_implicita is not None) else None
    return {
        "vinte": stat["vinte"], "perse": stat["perse"], "attesa": stat["attesa"],
        "concluse": concluse, "win_rate_%": win_rate,
        "quota_media_concluse": quota_media,
        "prob_implicita_media_%": prob_implicita,
        "edge_vs_implicita_%": edge_vs_implicita,
    }


def _e_reale_record(r: dict) -> bool:
    return (r.get("fonte") == "bet365_manuale"
            or str(r.get("nome", "")).startswith("PERSONALE_")
            or bool(r.get("giocata_reale")))


def _esito_reale_effettivo_record(r: dict):
    return r.get("esito_reale") or r.get("esito")


def costruisci_report_analitico(storico: list) -> dict:
    """Funzione pura (nessuna chiamata di rete): riceve la lista di schedine
    gia' lette da Firestore (leggi_storico_schedine) e produce un unico
    dizionario con tutti gli incroci utili a capire se/dove la Matrix ha un
    vantaggio reale, pensato per essere passato cosi' com'e' (es. in JSON) a
    chi deve decidere la strategia, non per essere mostrato in una UI:

    - per_fascia_quota: win rate per gamba, per fascia di quota, confrontato
      con la probabilita' implicita dalla quota stessa (1/quota) -- risponde
      alla domanda "conviene puntare singole ad alta probabilita'?".
    - per_famiglia_mercato: win rate per gamba, per tipo di mercato (1X2,
      Under/Over, ecc.), come la tabella gia' in app ma qui in dati grezzi.
    - per_numero_gambe: win rate a livello di SCHEDINA (tutte le proposte
      Matrix, non solo quelle giocate) raggruppato per quante gambe la
      compongono -- risponde alla domanda "le multiple con piu' gambe
      vincono davvero meno spesso?".
    - per_tier: win rate a livello di schedina per SAFETY/PERFORMANCE/
      AZZARDO/ALTRO, con P&L reale (puntato/saldo) quando disponibile.
    - per_lega: win rate per gamba raggruppato per campionato.
    - andamento_giornaliero: lista ordinata per data con vinte/perse
      (calcolo Matrix) e saldo reale del giorno.
    - riepilogo_reale: puntato/saldo/ROI complessivi sulle scommesse reali,
      e quante schedine hanno un esito_reale diverso da quello calcolato
      (indicatore di quanto spesso l'esecuzione reale diverge dal tip).
    """
    fascia_stats = {}
    famiglia_stats = {}
    lega_stats = {}
    numero_gambe_stats = {}
    tier_stats = {}
    giorno_stats = {}

    puntato_reale_tot = 0.0
    saldo_reale_tot = 0.0
    n_override_esito_reale = 0
    n_schedine_reali = 0

    for r in storico:
        selezioni = r.get("selezioni", [])
        for s in selezioni:
            q = s.get("quota")
            eg = s.get("esito_gamba")
            if q is not None:
                _registra_gamba(fascia_stats.setdefault(_fascia_quota(float(q)), _nuova_stat()), eg, q)
            tip_s = s.get("tip") or s.get("Tip") or ""
            if tip_s:
                _registra_gamba(famiglia_stats.setdefault(get_family(tip_s), _nuova_stat()), eg, q)
            lega_s = s.get("league") or "?"
            _registra_gamba(lega_stats.setdefault(lega_s, _nuova_stat()), eg, q)

        n_gambe = len(selezioni)
        chiave_n = str(n_gambe) if n_gambe < 6 else "6+"
        esito_calc = r.get("esito")
        stat_n = numero_gambe_stats.setdefault(chiave_n, {"vinte": 0, "perse": 0, "attesa": 0})
        if esito_calc == "vinta": stat_n["vinte"] += 1
        elif esito_calc == "persa": stat_n["perse"] += 1
        else: stat_n["attesa"] += 1

        nome_r = r.get("nome", "")
        tier = nome_r if nome_r in ("SAFETY", "PERFORMANCE", "AZZARDO") else "ALTRO"
        stat_t = tier_stats.setdefault(tier, {"vinte": 0, "perse": 0, "attesa": 0, "puntato": 0.0, "saldo": 0.0})
        if esito_calc == "vinta": stat_t["vinte"] += 1
        elif esito_calc == "persa": stat_t["perse"] += 1
        else: stat_t["attesa"] += 1

        if r.get("esito_reale"):
            n_override_esito_reale += 1

        data_r = r.get("data", "?")
        g = giorno_stats.setdefault(data_r, {"vinte": 0, "perse": 0, "attesa": 0, "saldo": 0.0})
        if esito_calc == "vinta": g["vinte"] += 1
        elif esito_calc == "persa": g["perse"] += 1
        else: g["attesa"] += 1

        if _e_reale_record(r):
            n_schedine_reali += 1
            p = r.get("puntata_reale")
            if p is not None:
                p = float(p)
                stat_t["puntato"] += p
                puntato_reale_tot += p
                esito_eff = _esito_reale_effettivo_record(r)
                saldo_riga = 0.0
                if esito_eff == "vinta":
                    vincita_reg = r.get("vincita_reale")
                    saldo_riga = (float(vincita_reg) - p) if vincita_reg is not None else (p * (r.get("quota_totale") or 0) - p)
                elif esito_eff == "persa":
                    saldo_riga = -p
                stat_t["saldo"] += saldo_riga
                saldo_reale_tot += saldo_riga
                g["saldo"] += saldo_riga

    return {
        "per_fascia_quota": {k: _finalizza_stat(v) for k, v in fascia_stats.items()},
        "per_famiglia_mercato": {k: _finalizza_stat(v) for k, v in famiglia_stats.items()},
        "per_lega": {k: _finalizza_stat(v) for k, v in lega_stats.items() if (v["vinte"] + v["perse"]) >= 3},
        "per_numero_gambe": {
            k: {**v, "concluse": v["vinte"] + v["perse"],
                "win_rate_%": round(v["vinte"] / (v["vinte"] + v["perse"]) * 100, 1) if (v["vinte"] + v["perse"]) else None}
            for k, v in numero_gambe_stats.items()
        },
        "per_tier": {
            k: {"vinte": v["vinte"], "perse": v["perse"], "attesa": v["attesa"],
                "concluse": v["vinte"] + v["perse"],
                "win_rate_%": round(v["vinte"] / (v["vinte"] + v["perse"]) * 100, 1) if (v["vinte"] + v["perse"]) else None,
                "puntato_reale": round(v["puntato"], 2), "saldo_reale": round(v["saldo"], 2)}
            for k, v in tier_stats.items()
        },
        "andamento_giornaliero": [
            {"data": data, **stat, "saldo": round(stat["saldo"], 2)}
            for data, stat in sorted(giorno_stats.items())
        ],
        "riepilogo_reale": {
            "n_schedine_reali": n_schedine_reali,
            "puntato_reale_tot": round(puntato_reale_tot, 2),
            "saldo_reale_tot": round(saldo_reale_tot, 2),
            "roi_%": round(saldo_reale_tot / puntato_reale_tot * 100, 1) if puntato_reale_tot else None,
            "n_override_esito_reale": n_override_esito_reale,
        },
        "n_schedine_totali": len(storico),
    }
