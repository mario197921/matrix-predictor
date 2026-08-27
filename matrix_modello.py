"""
matrix_modello.py — Motore di calcolo puro: Poisson/xG, quote, edge,
Kelly, generazione schedine. Nessuna funzione qui fa I/O (nessuna
chiamata di rete, nessun uso di streamlit) — sono tutte testabili in
isolamento con semplici assert su input/output.
"""

import itertools
import math

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
                                  max_prob_congiunta: float = None):
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
    massimizza comunque il valore, invece di ignorarlo del tutto."""
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
            sel.append(item); viste.add(nome)
            fam_cnt[fam] = fam_cnt.get(fam, 0) + 1
            if instabile: instabili_cnt += 1
            q_tot    *= float(item['Quota'])
            prob_tot *= item['Prob'] / 100.0
        if q_tot >= target_mult or len(sel) >= max_righe: break
    return sel, q_tot, prob_tot, viste.union(escludi_match)
