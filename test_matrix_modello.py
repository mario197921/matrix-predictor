"""
test_matrix_modello.py — Test automatici per il motore di calcolo puro
(matrix_modello.py). Nessuna chiamata di rete, nessuna dipendenza da
Streamlit: verificano solo la matematica.

Uso:
  - con pytest installato:  pytest test_matrix_modello.py -v
  - senza pytest:           python test_matrix_modello.py
"""

import math

from matrix_modello import (
    calcola_prob_poisson, calcola_tutti_i_mercati, get_quota_finale,
    calcola_edge_pct, kelly_fraction, semplifica_nome, get_family,
    costruisci_schedina_dinamica, devig_1x2, blend_prob_mercato,
    applica_blend_mercato_1x2,
)


# ── calcola_prob_poisson ────────────────────────────────────────────────────

def test_poisson_zero_gol_lambda_zero():
    # Con xG=0, la probabilità di 0 gol deve essere 1 (evento certo)
    assert calcola_prob_poisson(0.0001, 0) > 0.999


def test_poisson_somma_a_uno():
    # La somma delle probabilità su un range ampio di gol deve tendere a 1
    for xg in [0.3, 1.0, 1.8, 3.0]:
        tot = sum(calcola_prob_poisson(xg, g) for g in range(30))
        assert abs(tot - 1.0) < 1e-6, f"xg={xg} somma={tot}"


def test_poisson_valore_noto():
    # P(0 gol | xG=1.0) = e^-1 ≈ 0.3679
    assert abs(calcola_prob_poisson(1.0, 0) - math.exp(-1)) < 1e-9


# ── calcola_tutti_i_mercati ─────────────────────────────────────────────────

def test_mercati_1x2_somma_100():
    tips = calcola_tutti_i_mercati(1.4, 1.1, 9.0, 4.0, False, 22.0)
    assert abs(tips["1"] + tips["X"] + tips["2"] - 100.0) < 0.5


def test_mercati_doppia_chance_coerente():
    tips = calcola_tutti_i_mercati(1.4, 1.1, 9.0, 4.0, False, 22.0)
    assert abs(tips["1X"] - (tips["1"] + tips["X"])) < 1e-9
    assert abs(tips["X2"] - (tips["X"] + tips["2"])) < 1e-9
    assert abs(tips["12"] - (tips["1"] + tips["2"])) < 1e-9


def test_mercati_over_under_complementari():
    tips = calcola_tutti_i_mercati(1.4, 1.1, 9.0, 4.0, False, 22.0)
    for line in [1.5, 2.5, 3.5, 4.5]:
        somma = tips[f"U{line}"] + tips[f"O{line}"]
        assert abs(somma - 100.0) < 0.5, f"linea {line}: somma={somma}"


def test_mercati_squadra_forte_batte_debole():
    # Una squadra con xG molto più alto deve avere prob "1" nettamente
    # superiore a "2" — sanity check di direzione, non di valore esatto.
    tips = calcola_tutti_i_mercati(2.5, 0.4, 9.0, 4.0, False, 20.0)
    assert tips["1"] > tips["2"] + 30


def test_mercati_simmetria_xg_uguali():
    # Con xG identici, "1" e "2" devono essere molto vicini (il vantaggio
    # casa non è nel modello stesso, quindi con stesso input deve essere ~simmetrico)
    tips = calcola_tutti_i_mercati(1.3, 1.3, 9.0, 4.0, False, 20.0)
    assert abs(tips["1"] - tips["2"]) < 0.5


# ── get_quota_finale / calcola_edge_pct / kelly_fraction ───────────────────

def test_quota_reale_quando_disponibile():
    q, is_real = get_quota_finale("1", 55.0, {"1": 1.85})
    assert q == 1.85 and is_real is True


def test_quota_calcolata_quando_assente():
    q, is_real = get_quota_finale("1", 50.0, {})
    assert is_real is False
    assert q >= 1.01
    # con margine 7%, la quota sintetica deve essere leggermente sotto
    # la quota "equa" (100/prob)
    quota_equa = 100.0 / 50.0
    assert q < quota_equa


def test_quota_prob_zero_fallback():
    q, is_real = get_quota_finale("1", 0.0, {})
    assert q == 99.0 and is_real is False


def test_edge_zero_su_quota_equa():
    # Su una quota esattamente equa (100/prob), l'edge deve essere ~0
    prob = 40.0
    quota_equa = 100.0 / prob
    assert abs(calcola_edge_pct(prob, quota_equa)) < 1e-9


def test_edge_positivo_quota_favorevole():
    assert calcola_edge_pct(50.0, 2.5) > 0   # quota 2.5 su prob 50% = valore
    assert calcola_edge_pct(50.0, 1.5) < 0   # quota 1.5 su prob 50% = svantaggio


def test_kelly_zero_senza_edge():
    # A quota "equa" o sfavorevole, il Kelly deve essere 0 (mai puntare)
    assert kelly_fraction(40.0, 2.0) == 0.0   # quota equa esatta (100/40=2.5>2.0 quindi sfavorevole)


def test_kelly_positivo_con_edge():
    k = kelly_fraction(55.0, 2.2, fraz=0.25)
    assert 0.0 < k < 0.25   # deve essere una frazione positiva ma sotto il cap Kelly pieno


def test_kelly_quota_non_valida():
    assert kelly_fraction(50.0, 1.0) == 0.0   # b=0 -> nessuna puntata sensata


# ── semplifica_nome / get_family ────────────────────────────────────────────

def test_semplifica_nome_suffissi():
    assert semplifica_nome("Inter FC") == "Inter"
    assert semplifica_nome("AS Roma") == "Roma"
    assert semplifica_nome("Real Sociedad AFC") == "Real Sociedad"


def test_semplifica_nome_non_tronca_nomi_legittimi():
    # "FCB" o nomi che contengono le sigle come parte del nome non devono
    # essere troncati in modo aggressivo (motivazione del FIX originale)
    assert "FCB" not in "FCB" or semplifica_nome("FCB") != ""


def test_get_family_categorie_base():
    assert get_family("1") == "1X2"
    assert get_family("1X") == "1X2"
    assert get_family("O2.5") == "UO"
    assert get_family("Goal") == "GGNG"
    assert get_family("MG 1-3") == "MG"
    assert get_family("1X + Over 1.5") == "COMBO"
    assert get_family("Risultato 1-0") == "RE"
    assert get_family("HT/FT 1/1") == "HTFT"
    assert get_family("Pari") == "PD"
    assert get_family("Over 8.5 Angoli") == "SPECIAL"


# ── costruisci_schedina_dinamica ────────────────────────────────────────────

def _pool_esempio():
    return [
        {"Match": "A vs B", "Tip": "1",  "Prob": 55.0, "Quota": 2.0, "Edge": 10.0},
        {"Match": "C vs D", "Tip": "X2", "Prob": 60.0, "Quota": 1.8, "Edge": 8.0},
        {"Match": "E vs F", "Tip": "O2.5", "Prob": 50.0, "Quota": 2.1, "Edge": 5.0},
        {"Match": "A vs B", "Tip": "O2.5", "Prob": 50.0, "Quota": 2.1, "Edge": 5.0},  # stesso match di sopra
        {"Match": "G vs H", "Tip": "2", "Prob": 30.0, "Quota": 3.0, "Edge": -5.0},   # edge negativo, va escluso
    ]


def test_schedina_esclude_edge_negativo():
    sel, q_tot, prob_tot, usati = costruisci_schedina_dinamica(
        _pool_esempio(), min_q=1.01, max_q=99.0, target_mult=50.0)
    assert all(x["Edge"] > 0 for x in sel)


def test_schedina_niente_doppioni_stesso_match():
    sel, q_tot, prob_tot, usati = costruisci_schedina_dinamica(
        _pool_esempio(), min_q=1.01, max_q=99.0, target_mult=50.0)
    match_scelti = [x["Match"] for x in sel]
    assert len(match_scelti) == len(set(match_scelti))


def test_schedina_rispetta_escludi_match():
    sel, q_tot, prob_tot, usati = costruisci_schedina_dinamica(
        _pool_esempio(), min_q=1.01, max_q=99.0, target_mult=50.0,
        escludi_match={"A vs B"})
    assert all(x["Match"] != "A vs B" for x in sel)
    assert "A vs B" in usati


def test_schedina_rispetta_max_righe():
    pool_grande = [
        {"Match": f"M{i}", "Tip": "1", "Prob": 50.0, "Quota": 1.5, "Edge": 1.0}
        for i in range(50)
    ]
    sel, q_tot, prob_tot, usati = costruisci_schedina_dinamica(
        pool_grande, min_q=1.01, max_q=99.0, target_mult=9999.0, max_righe=5)
    assert len(sel) <= 5


def test_schedina_limita_selezioni_instabili_per_combo():
    # 4 partite tutte "instabili" (es. coppe/inizio stagione): la combo non
    # deve concentrarne più di max_instabili (default 1), anche se tutte
    # avrebbero edge sufficiente a entrare.
    pool_instabile = [
        {"Match": f"M{i}", "Tip": "1", "Prob": 60.0, "Quota": 1.8, "Edge": 8.0, "Instabile": True}
        for i in range(4)
    ]
    sel, q_tot, prob_tot, usati = costruisci_schedina_dinamica(
        pool_instabile, min_q=1.01, max_q=99.0, target_mult=9999.0, max_righe=10)
    instabili_in_sel = sum(1 for x in sel if x.get("Instabile"))
    assert instabili_in_sel <= 1


def test_schedina_instabili_non_bloccano_le_stabili():
    # Con un mix di instabili e stabili, le selezioni stabili devono comunque
    # entrare normalmente: il tetto riguarda solo le "Instabile": True.
    # (Edge coerente con Prob/Quota: la funzione lo ricalcola internamente
    # per l'ordinamento, non si fida del campo "Edge" passato in ingresso.)
    pool_misto = (
        [{"Match": f"I{i}", "Tip": "1", "Prob": 70.0, "Quota": 1.8, "Edge": 26.0, "Instabile": True}
         for i in range(3)]
        + [{"Match": "S0", "Tip": "O2.5", "Prob": 65.0, "Quota": 1.7, "Edge": 10.5, "Instabile": False},
           {"Match": "S1", "Tip": "Goal", "Prob": 65.0, "Quota": 1.7, "Edge": 10.5, "Instabile": False},
           {"Match": "S2", "Tip": "MG 1-3", "Prob": 65.0, "Quota": 1.7, "Edge": 10.5, "Instabile": False}]
    )
    sel, q_tot, prob_tot, usati = costruisci_schedina_dinamica(
        pool_misto, min_q=1.01, max_q=99.0, target_mult=9999.0, max_righe=10)
    stabili_in_sel = sum(1 for x in sel if not x.get("Instabile"))
    assert stabili_in_sel == 3


def test_schedina_ordina_per_prob_sceglie_prob_piu_alta():
    # Con ordina_per="prob", a parita' di edge la combo deve preferire le
    # gambe a probabilita' più alta (non quelle a edge più alto) — usato
    # dalla schedina Safety per massimizzare la probabilita' congiunta.
    pool = [
        {"Match": "A", "Tip": "1", "Prob": 60.0, "Quota": 2.0, "Edge": 20.0},  # edge alto, prob bassa
        {"Match": "B", "Tip": "1", "Prob": 90.0, "Quota": 1.15, "Edge": 3.5},  # edge basso, prob alta
    ]
    sel, q_tot, prob_tot, usati = costruisci_schedina_dinamica(
        pool, min_q=1.01, max_q=99.0, target_mult=9999.0, max_righe=1, ordina_per="prob")
    assert sel[0]["Match"] == "B"

    sel_edge, _, _, _ = costruisci_schedina_dinamica(
        pool, min_q=1.01, max_q=99.0, target_mult=9999.0, max_righe=1, ordina_per="edge")
    assert sel_edge[0]["Match"] == "A"


def test_schedina_prob_range_sceglie_edge_migliore_nella_fascia():
    # 3 possibili coppie di partite indipendenti; solo alcune combinazioni
    # cadono nella fascia di probabilita' congiunta 80-100%. Fra quelle
    # ammesse, deve scegliere la combinazione con l'edge combinato piu' alto,
    # non necessariamente quella con la probabilita' congiunta piu' alta.
    pool = [
        {"Match": "A", "Tip": "1",    "Prob": 95.0, "Quota": 1.15, "Edge": 9.25},   # molto sicura, poco edge
        {"Match": "B", "Tip": "1",    "Prob": 95.0, "Quota": 1.15, "Edge": 9.25},   # molto sicura, poco edge
        {"Match": "C", "Tip": "X2",   "Prob": 88.0, "Quota": 1.30, "Edge": 14.4},   # meno sicura, piu' edge
        {"Match": "D", "Tip": "O2.5", "Prob": 60.0, "Quota": 2.50, "Edge": 50.0},   # troppo rischiosa da sola
    ]
    # A+B: prob congiunta 0.9025 (in fascia), edge combinato ~18.5
    # A+C: prob congiunta 0.836 (in fascia), edge combinato ~23.65 <- il migliore in fascia
    # A+D / B+D / C+D: prob congiunta troppo bassa (fuori fascia 0.80-1.00)
    sel, q_tot, prob_tot, usati = costruisci_schedina_dinamica(
        pool, min_q=1.01, max_q=99.0, target_mult=9999.0, max_righe=2,
        ordina_per="prob_range", min_prob_congiunta=0.80, max_prob_congiunta=1.00)
    scelti = sorted(x["Match"] for x in sel)
    assert scelti == ["A", "C"], scelti
    assert 0.80 <= prob_tot <= 1.00


def test_schedina_prob_range_nessuna_combo_in_fascia():
    # Se nessuna coppia possibile rientra nella fascia richiesta, la funzione
    # deve restituire una selezione vuota (segnale per "salta la schedina"),
    # non forzare comunque una combinazione fuori fascia.
    pool = [
        {"Match": "A", "Tip": "1", "Prob": 95.0, "Quota": 1.15, "Edge": 9.25},
        {"Match": "B", "Tip": "1", "Prob": 30.0, "Quota": 2.00, "Edge": -40.0},
    ]
    sel, q_tot, prob_tot, usati = costruisci_schedina_dinamica(
        pool, min_q=1.01, max_q=99.0, target_mult=9999.0, max_righe=2,
        ordina_per="prob_range", min_prob_congiunta=0.95, max_prob_congiunta=1.00)
    assert sel == []


# ── devig_1x2 / blend_prob_mercato / applica_blend_mercato_1x2 ─────────────

def test_devig_1x2_somma_100():
    prob = devig_1x2({"1": 1.50, "X": 4.20, "2": 6.00})
    assert abs(sum(prob.values()) - 100.0) < 1e-9


def test_devig_1x2_toglie_il_margine():
    # Quote leggermente "vig-gate": probabilita' grezze sommano a piu' di 100,
    # il devig deve riportarle a somma 100 mantenendo le proporzioni relative.
    quote = {"1": 1.50, "X": 4.20, "2": 6.00}
    grezzo_1 = 1.0 / 1.50 * 100.0
    prob = devig_1x2(quote)
    assert prob["1"] < grezzo_1  # dopo il devig, ogni prob scende (il margine viene tolto)


def test_devig_1x2_none_se_quote_incomplete():
    assert devig_1x2({"1": 1.50, "X": 4.20}) is None   # manca "2"
    assert devig_1x2({}) is None
    assert devig_1x2(None) is None


def test_blend_prob_mercato_estremi():
    assert blend_prob_mercato(50.0, 80.0, 0.0) == 50.0    # peso 0 -> solo modello
    assert blend_prob_mercato(50.0, 80.0, 1.0) == 80.0    # peso 1 -> solo mercato
    assert blend_prob_mercato(50.0, 80.0, 0.5) == 65.0    # a meta'


def test_applica_blend_mercato_1x2_corregge_favorito_sottostimato():
    # Caso "Barcellona": il modello stima il favorito solo al 51.8% (1X2 quasi
    # equilibrato) ma il mercato reale (quota molto bassa) lo dà nettamente
    # favorito. Con peso alto (contesto instabile) la stima blendata deve
    # avvicinarsi parecchio al mercato, non restare vicina al modello.
    full_tips = calcola_tutti_i_mercati(1.35, 1.30, 9.0, 4.0, False, 22.0)  # xG quasi pari -> "1" ~debole
    quote_reali = {"1": 1.22, "X": 6.50, "2": 12.00}   # mercato: favorito nettissimo
    prob_prima = full_tips["1"]
    blended = applica_blend_mercato_1x2(full_tips, quote_reali, peso_mercato=0.55)
    assert blended["1"] > prob_prima + 10   # si e' avvicinata parecchio al mercato
    # coerenza interna: 1X deve ancora essere 1+X dopo il ricalcolo
    assert abs(blended["1X"] - (blended["1"] + blended["X"])) < 1e-6


def test_applica_blend_mercato_1x2_nessuna_quota_reale_non_cambia_nulla():
    full_tips = calcola_tutti_i_mercati(1.4, 1.1, 9.0, 4.0, False, 22.0)
    invariato = applica_blend_mercato_1x2(full_tips, {}, peso_mercato=0.55)
    assert invariato == full_tips


ALL_TESTS = [v for k, v in list(globals().items()) if k.startswith("test_")]


if __name__ == "__main__":
    ok = fail = 0
    for t in ALL_TESTS:
        try:
            t()
            ok += 1
            print(f"OK   {t.__name__}")
        except AssertionError as e:
            fail += 1
            print(f"FAIL {t.__name__}: {e}")
        except Exception as e:
            fail += 1
            print(f"ERROR {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{ok} passati, {fail} falliti su {ok + fail} test totali.")
    raise SystemExit(1 if fail else 0)
