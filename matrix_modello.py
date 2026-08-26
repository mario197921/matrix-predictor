"""
matrix_modello.py — Motore di calcolo puro: Poisson/xG, quote, edge,
Kelly, generazione schedine. Nessuna funzione qui fa I/O (nessuna
chiamata di rete, nessun uso di streamlit) — sono tutte testabili in
isolamento con semplici assert su input/output.
"""

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

def kelly_fraction(prob: float, quota: float, fraz: float = 0.25) -> float:
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
