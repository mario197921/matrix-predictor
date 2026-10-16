"""Genera tests_js/golden.json eseguendo il modello PYTHON su input casuali
(seed fisso). Il test Node confronta l'output del port JS con questi valori."""
import json, random, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import matrix_modello as M

rnd = random.Random(12345)
G = {}

# 1) mercati
casi = []
for _ in range(25):
    a = [round(rnd.uniform(0.2, 3.2), 3), round(rnd.uniform(0.2, 3.2), 3),
         round(rnd.uniform(5, 14), 2), round(rnd.uniform(1, 8), 2), rnd.random() < 0.3, round(rnd.uniform(15, 40), 1)]
    out = M.calcola_tutti_i_mercati(*a)
    casi.append({"args": a, "out": [[k, v] for k, v in out.items()]})
G["mercati"] = casi

# 2) blend
casi = []
for c in G["mercati"][:10]:
    full = dict((k, v) for k, v in c["out"])
    q = {"1": round(rnd.uniform(1.2, 4), 2), "X": round(rnd.uniform(2.8, 4.5), 2), "2": round(rnd.uniform(1.5, 8), 2)}
    for peso in (0.15, 0.55):
        out = M.applica_blend_mercato_1x2(full, q, peso)
        casi.append({"full": c["out"], "q": q, "peso": peso, "out": [[k, v] for k, v in out.items()]})
    casi.append({"full": c["out"], "q": {"1": 2.0}, "peso": 0.5, "out": [[k, v] for k, v in M.applica_blend_mercato_1x2(full, {"1": 2.0}, 0.5).items()]})
G["blend"] = casi

# 3) quota finale / edge / kelly
casi = []
for _ in range(40):
    prob = round(rnd.uniform(0, 95), 3)
    reali = {"1": 1.9, "O2.5": 2.05} if rnd.random() < 0.5 else {}
    tip = rnd.choice(["1", "O2.5", "X", "U3.5"])
    q, real = M.get_quota_finale(tip, prob, reali)
    casi.append({"tip": tip, "prob": prob, "reali": reali, "q": q, "real": real,
                 "edge": M.calcola_edge_pct(prob, q), "kelly": M.kelly_fraction(prob, q)})
G["quota"] = casi

# 4) schedine
TIPS = list(G["mercati"][0]["out"])
pool_casi = []
for caso in range(30):
    pool = []
    for i in range(rnd.randint(8, 70)):
        tip = rnd.choice([t[0] for t in TIPS])
        prob = round(rnd.uniform(20, 92), 2)
        real = rnd.random() < 0.6
        quota = round(rnd.uniform(1.05, 5.5), 2)
        pool.append({"Match": f"M{rnd.randint(1, 30)}", "Tip": tip, "Prob": prob, "Quota": quota, "Real": real,
                     "Edge": M.calcola_edge_pct(prob, quota), "Instabile": rnd.random() < 0.2, "id": i})
    for params in [
        dict(min_q=1.12, max_q=1.5, target_mult=2.0, max_match_q=2.0, max_righe=3, ordina_per="edge", solo_edge_positivo=True),
        dict(min_q=1.51, max_q=2.2, target_mult=5.0, max_match_q=2.2, max_righe=12, ordina_per="edge"),
        dict(min_q=2.21, max_q=4.5, target_mult=30.0, max_match_q=4.5, max_righe=12, ordina_per="edge", max_quota_finale=50.0),
        dict(min_q=1.12, max_q=1.5, target_mult=2.0, max_match_q=2.0, max_righe=3, ordina_per="prob", solo_edge_positivo=False, solo_quote_reali=True),
        dict(min_q=1.51, max_q=2.2, target_mult=5.0, max_match_q=2.2, max_righe=12, ordina_per="prob", solo_edge_positivo=False, solo_quote_reali=True),
        dict(min_q=2.21, max_q=4.5, target_mult=30.0, max_match_q=4.5, max_righe=12, ordina_per="prob", solo_edge_positivo=False, solo_quote_reali=True, max_quota_finale=50.0),
        dict(min_q=1.2, max_q=2.0, target_mult=3.0, max_match_q=5.0, max_righe=2, ordina_per="prob_range", min_prob_congiunta=0.2, max_prob_congiunta=0.9),
    ]:
        escl = {f"M{rnd.randint(1,30)}"} if rnd.random() < 0.3 else set()
        sel, q, p, usati = M.costruisci_schedina_dinamica(pool, params.pop("min_q"), params.pop("max_q"), params.pop("target_mult"),
                                                         escludi_match=escl, **params)
        pool_casi.append({"pool": pool, "escludi": sorted(escl), "params": None, "ids": [s["id"] for s in sel], "q": q, "p": p, "usati": sorted(usati)})
        pool_casi[-1]["params"] = None
# memorizza i parametri originali (ricostruiti)
G["_note"] = "params ricostruiti nel test"
# per semplicita' i parametri vengono rigenerati: salviamoli esplicitamente
pool_casi = []
rnd2 = random.Random(777)
PARAMS = [
    dict(minQ=1.12, maxQ=1.5, target=2.0, maxMatchQ=2.0, maxRighe=3, ordinaPer="edge", soloEdgePositivo=True),
    dict(minQ=1.51, maxQ=2.2, target=5.0, maxMatchQ=2.2, maxRighe=12, ordinaPer="edge"),
    dict(minQ=2.21, maxQ=4.5, target=30.0, maxMatchQ=4.5, maxRighe=12, ordinaPer="edge", maxQuotaFinale=50.0),
    dict(minQ=1.12, maxQ=1.5, target=2.0, maxMatchQ=2.0, maxRighe=3, ordinaPer="prob", soloEdgePositivo=False, soloQuoteReali=True),
    dict(minQ=1.51, maxQ=2.2, target=5.0, maxMatchQ=2.2, maxRighe=12, ordinaPer="prob", soloEdgePositivo=False, soloQuoteReali=True),
    dict(minQ=2.21, maxQ=4.5, target=30.0, maxMatchQ=4.5, maxRighe=12, ordinaPer="prob", soloEdgePositivo=False, soloQuoteReali=True, maxQuotaFinale=50.0),
    dict(minQ=1.2, maxQ=2.0, target=3.0, maxMatchQ=5.0, maxRighe=2, ordinaPer="prob_range", minProbCongiunta=0.2, maxProbCongiunta=0.9),
]
SNAKE = {"minQ": "min_q", "maxQ": "max_q", "target": "target_mult", "maxMatchQ": "max_match_q", "maxRighe": "max_righe",
         "ordinaPer": "ordina_per", "soloEdgePositivo": "solo_edge_positivo", "soloQuoteReali": "solo_quote_reali",
         "maxQuotaFinale": "max_quota_finale", "minProbCongiunta": "min_prob_congiunta", "maxProbCongiunta": "max_prob_congiunta"}
for caso in range(40):
    pool = []
    for i in range(rnd2.randint(8, 70)):
        tip = rnd2.choice([t[0] for t in TIPS])
        prob = round(rnd2.uniform(20, 92), 2)
        quota = round(rnd2.uniform(1.05, 5.5), 2)
        pool.append({"Match": f"M{rnd2.randint(1, 30)}", "Tip": tip, "Prob": prob, "Quota": quota, "Real": rnd2.random() < 0.6,
                     "Edge": M.calcola_edge_pct(prob, quota), "Instabile": rnd2.random() < 0.2, "id": i})
    for params in PARAMS:
        escl = {f"M{rnd2.randint(1,30)}"} if rnd2.random() < 0.3 else set()
        kw = {SNAKE[k]: v for k, v in params.items()}
        min_q = kw.pop("min_q"); max_q = kw.pop("max_q"); tgt = kw.pop("target_mult")
        sel, q, p, usati = M.costruisci_schedina_dinamica(pool, min_q, max_q, tgt, escludi_match=escl, **kw)
        pool_casi.append({"pool": pool, "escludi": sorted(escl), "params": params,
                          "ids": [s["id"] for s in sel], "q": q, "p": p, "usati": sorted(usati)})
G["schedine"] = pool_casi

# 5) esiti
esiti = []
tips = [t[0] for t in TIPS] + ["Over 8.5 Angoli", "Strano", "Casa O0.5", "Ospite O0.5"]
for tip in tips:
    for gc, gt, hc, ht in [(0, 0, 0, 0), (1, 0, 0, 0), (2, 1, 1, 0), (3, 3, 1, 2), (0, 4, 0, 1), (2, 2, None, None), (5, 0, 2, 0), (1, 1, 0, 1)]:
        esiti.append({"tip": tip, "args": [gc, gt, hc, ht], "out": M.valuta_esito_tip(tip, gc, gt, hc, ht)})
G["esiti"] = esiti

# 6) utility
G["famiglie"] = [[t, M.get_family(t)] for t in tips + ["U4.5", "Goal + Over 2.5", "O0.5"]]
G["nomi"] = [[n, M.semplifica_nome(n)] for n in ["FC Bayern", "Inter FC", "AC Milan", "AFC Ajax", "Real Madrid CF SL", "Sporting AS", "  Roma Calcio  "]]
G["prior"] = [[cur, prev, g, M.blend_prior_stagione(cur, prev, g)] for cur, prev, g in
              [(1.5, 1.2, 0), (1.5, 1.2, 5), (1.5, 1.2, 12), (1.0, None, 3)]]

# 7) storico: report + simulazione
nomi = ["SAFETY", "PERFORMANCE", "AZZARDO", "PROB_SAFETY", "PROB_PERFORMANCE", "PROB_AZZARDO", "PERSONALE_101010", "ALTRO_X"]
storico = []
rnd3 = random.Random(99)
for i in range(120):
    nome = rnd3.choice(nomi)
    n_gambe = rnd3.randint(0, 8)
    sel = []
    for j in range(n_gambe):
        sel.append({"match": f"A{j} vs B{j}", "tip": rnd3.choice(tips), "quota": round(rnd3.uniform(1.05, 6), 2),
                    "league": rnd3.choice(["Serie A", "Liga", "?", "MLS"]),
                    "esito_gamba": rnd3.choice(["vinta", "persa", None, None])})
    if rnd3.random() < 0.15:
        data = f"storico_{rnd3.randint(1, 30):02d}"
    else:
        data = f"2026-{rnd3.randint(8, 10):02d}-{rnd3.randint(1, 28):02d}"
    rec = {"nome": nome, "data": data, "selezioni": sel,
           "esito": rnd3.choice(["vinta", "persa", "in_attesa"]),
           "quota_totale": rnd3.choice([None, 0, round(rnd3.uniform(1.1, 40), 2)]),
           "probabilita_congiunta": 0.2, "budget": 5.0}
    if rnd3.random() < 0.5: rec["metodo"] = rnd3.choice(["prob", "edge"])
    if nome.startswith("PERSONALE") or rnd3.random() < 0.3:
        if rnd3.random() < 0.3: rec["fonte"] = "bet365_manuale"
        rec["giocata_reale"] = True
        if rnd3.random() < 0.8: rec["puntata_reale"] = rnd3.choice([0.5, 1.0, 2.0])
        if rnd3.random() < 0.3: rec["esito_reale"] = rnd3.choice(["vinta", "persa"])
        if rnd3.random() < 0.3: rec["vincita_reale"] = round(rnd3.uniform(1, 30), 2)
    storico.append(rec)
G["storico"] = storico
G["report"] = M.costruisci_report_analitico(storico, budget_iniziale=10.0)
G["report0"] = M.costruisci_report_analitico(storico)
G["sim"] = M.simula_bankroll_virtuale(storico, puntata=1.0, bankroll_iniziale=10.0)
G["sim2"] = M.simula_bankroll_virtuale(storico, puntata=2.5, bankroll_iniziale=3.0)

# 8) record
G["record"] = M.costruisci_record_schedina("PROB_SAFETY", "2026-10-16",
    [{"Match": "A vs B", "Tip": "1", "Prob": 62.345, "Quota": 1.456, "Edge": 3.456, "League": "Serie A", "FixtureID": 99},
     {"Match": "C vs D", "Tip": "O2.5", "Prob": 55.0, "Quota": 1.8}], 2.62, 0.343, 5.0, creato_il="X", metodo="prob")
json.dump(G, open(os.path.join(os.path.dirname(__file__), 'golden.json'), 'w'), ensure_ascii=False)
print("golden generato:", {k: (len(v) if hasattr(v, '__len__') else v) for k, v in G.items()})
