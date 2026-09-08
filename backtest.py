"""
backtest.py — Backtest storico del motore Poisson/Kelly di Matrix Bet V90
contro risultati reali (CSV gratuiti da football-data.co.uk).

COSA TESTA E COSA NO (leggi prima di interpretare i risultati)
----------------------------------------------------------------
Questo script usa le STESSE funzioni di produzione di matrix_modello.py
(calcola_tutti_i_mercati, get_quota_finale, calcola_edge_pct,
kelly_fraction) — non una riscrittura — quindi il motore Poisson/Kelly
testato qui è esattamente quello che gira nell'app.

Lo xG in ingresso è un PROXY che replica la stessa struttura usata da
app.py per le partite di campionato "normali": un blend 70% standings
(media gol fatti/subiti in casa/trasferta da inizio stagione, come
db_stats['ac']/['dc']/['at']/['dt']) + 30% momentum (media sulle ultime
N partite, come xg_mo_c/xg_mo_t) — stesso peso_std/peso_mom di app.py
(righe ~2023-2026). Tutto calcolato SOLO su partite già giocate nel CSV
prima di quella in esame (nessun look-ahead), stagione per stagione
(le statistiche ripartono da zero a ogni nuovo file CSV, non si
mescolano tra stagioni diverse).

Quello che NON include, perché richiede l'API live e non è
backtestabile sul passato senza un archivio storico dedicato:
infortuni, H2H/andata, motivazione/pressione classifica, meteo,
arbitro, correttivi di lega (mal_lega), boost coppa/playoff — tutta la
parte che nell'app vive nel loop principale sopra il blend di xG di
base. Un risultato qui dice quindi "il motore Poisson + il blend
standings/momentum di base sono calibrati", non "l'app intera con
tutti i correttivi è profittevole".

USO
----
1. Scarica qualche CSV storico da football-data.co.uk, es.:
     https://www.football-data.co.uk/mmz4281/2425/E0.csv   (Premier League 24/25)
     https://www.football-data.co.uk/mmz4281/2425/I1.csv   (Serie A 24/25)
     https://www.football-data.co.uk/mmz4281/2425/SP1.csv  (Liga 24/25)
     https://www.football-data.co.uk/mmz4281/2425/D1.csv   (Bundesliga 24/25)
     https://www.football-data.co.uk/mmz4281/2425/F1.csv   (Ligue 1 24/25)
   (cambia "2425" con altre stagioni, es. "2324", "2223", per più dati)
2. Mettili in una sottocartella, es. backtest_data/*.csv
3. python backtest.py backtest_data/

Nessuna dipendenza esterna oltre a pandas (già nei requirements.txt
del progetto).
"""

import glob
import math
import sys
from collections import defaultdict, deque

import pandas as pd

from matrix_modello import (
    calcola_tutti_i_mercati, calcola_edge_pct,
    kelly_fraction, semplifica_nome,
)

XG_MIN, XG_MAX = 0.10, 3.2
FINESTRA_ROLLING = 6          # ultime N partite per la media gol casa/trasferta
QUOTA_CAP = 6.0                # tetto massimo alla quota su cui si scommette (correzione
                                # empirica: oltre questa soglia il modello sovrastima
                                # sistematicamente l'edge, vedi nota in fondo al file)
QUOTE_COLONNE_PRIORITA = [
    ("B365H", "B365D", "B365A"),
    ("BWH", "BWD", "BWA"),
    ("IWH", "IWD", "IWA"),
    ("PSH", "PSD", "PSA"),
    ("AvgH", "AvgD", "AvgA"),
]
QUOTE_OU25_COLONNE_PRIORITA = [
    ("B365>2.5", "B365<2.5"),
    ("P>2.5", "P<2.5"),
    ("Avg>2.5", "Avg<2.5"),
]


def carica_csv(cartella: str) -> pd.DataFrame:
    file_csv = sorted(glob.glob(f"{cartella.rstrip('/')}/*.csv"))
    if not file_csv:
        raise SystemExit(f"Nessun CSV trovato in '{cartella}'. "
                          f"Scarica qualche file da football-data.co.uk e riprova.")
    frames = []
    for path in file_csv:
        try:
            df = pd.read_csv(path, encoding="latin1")
        except Exception as e:
            print(f"⚠️  Salto {path}: {e}")
            continue
        richieste = {"Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"}
        if not richieste.issubset(df.columns):
            print(f"⚠️  Salto {path}: mancano colonne obbligatorie {richieste - set(df.columns)}")
            continue
        df["__file__"] = path
        frames.append(df)
    if not frames:
        raise SystemExit("Nessun CSV valido (colonne mancanti in tutti i file).")
    tutte = pd.concat(frames, ignore_index=True, sort=False)
    tutte["Date"] = pd.to_datetime(tutte["Date"], dayfirst=True, errors="coerce")
    tutte = tutte.dropna(subset=["Date", "FTHG", "FTAG"])
    tutte = tutte.sort_values("Date").reset_index(drop=True)
    return tutte


def trova_colonne_quote(df: pd.DataFrame):
    for h, d, a in QUOTE_COLONNE_PRIORITA:
        if {h, d, a}.issubset(df.columns):
            return h, d, a
    return None


def trova_colonne_quote_ou25(df: pd.DataFrame):
    for over, under in QUOTE_OU25_COLONNE_PRIORITA:
        if {over, under}.issubset(df.columns):
            return over, under
    return None


PESO_MOM = 0.30   # stesso peso di app.py per le partite di campionato "normali"
PESO_STD = 1.0 - PESO_MOM
MIN_PARTITE_STANDINGS = 3   # minimo di partite casa/trasferta per fidarsi della media stagionale


def _nuovo_stato_squadra():
    return {
        "casa": deque(maxlen=FINESTRA_ROLLING), "trasferta": deque(maxlen=FINESTRA_ROLLING),
        "cum_casa_gf": 0, "cum_casa_gs": 0, "n_casa": 0,
        "cum_trasf_gf": 0, "cum_trasf_gs": 0, "n_trasf": 0,
    }


def stima_xg(storico_stagione: dict, casa: str, ospite: str):
    """Blend 70% standings (media stagionale casa/trasferta) + 30% momentum
    (ultime FINESTRA_ROLLING partite) — stessa struttura di app.py per le
    partite di campionato normali. Usa SOLO partite già giocate (nessun
    look-ahead); richiede un minimo storico per entrambe le componenti."""
    st_c = storico_stagione[casa]
    st_t = storico_stagione[ospite]
    if (st_c["n_casa"] < MIN_PARTITE_STANDINGS or st_t["n_trasf"] < MIN_PARTITE_STANDINGS
            or len(st_c["casa"]) < FINESTRA_ROLLING or len(st_t["trasferta"]) < FINESTRA_ROLLING):
        return None, None   # warm-up insufficiente

    # Componente standings (media stagionale da inizio stagione ad oggi)
    ac = st_c["cum_casa_gf"] / st_c["n_casa"]
    dc = st_c["cum_casa_gs"] / st_c["n_casa"]
    at = st_t["cum_trasf_gf"] / st_t["n_trasf"]
    dt = st_t["cum_trasf_gs"] / st_t["n_trasf"]
    xg_st_c = math.sqrt(max(0.01, ac) * max(0.01, dt))
    xg_st_t = math.sqrt(max(0.01, at) * max(0.01, dc))

    # Componente momentum (ultime FINESTRA_ROLLING partite)
    def media(dq, chiave):
        vals = [m[chiave] for m in dq]
        return sum(vals) / len(vals)

    gf_home_c = media(st_c["casa"], "gf");  gs_home_c = media(st_c["casa"], "gs")
    gf_away_t = media(st_t["trasferta"], "gf"); gs_away_t = media(st_t["trasferta"], "gs")
    xg_mo_c = math.sqrt(max(0.01, gf_home_c) * max(0.01, gs_away_t))
    xg_mo_t = math.sqrt(max(0.01, gf_away_t) * max(0.01, gs_home_c))

    xg_c = xg_st_c * PESO_STD + xg_mo_c * PESO_MOM
    xg_t = xg_st_t * PESO_STD + xg_mo_t * PESO_MOM
    xg_c = min(XG_MAX, max(XG_MIN, xg_c))
    xg_t = min(XG_MAX, max(XG_MIN, xg_t))
    return xg_c, xg_t


def esegui_backtest(cartella: str):
    df = carica_csv(cartella)
    print(f"Caricate {len(df)} partite da {df['__file__'].nunique()} file "
          f"({df['Date'].min().date()} → {df['Date'].max().date()})\n")

    # Storico separato per stagione (file CSV): niente mescolanza tra stagioni diverse.
    storico_per_stagione = defaultdict(lambda: defaultdict(_nuovo_stato_squadra))

    valutazioni = []   # una riga per (partita, mercato valutato)
    bilancio_flat = bilancio_kelly = 0.0
    budget_kelly = 100.0   # unità di bankroll iniziale per il simulatore Kelly
    puntate = []

    for _, riga in df.iterrows():
        stagione_key = riga["__file__"]
        storico = storico_per_stagione[stagione_key]
        casa = semplifica_nome(str(riga["HomeTeam"]))
        ospite = semplifica_nome(str(riga["AwayTeam"]))
        gf_c, gf_t = int(riga["FTHG"]), int(riga["FTAG"])

        xg_c, xg_t = stima_xg(storico, casa, ospite)
        if xg_c is not None:
            tips = calcola_tutti_i_mercati(xg_c, xg_t, 9.0, 4.0, False, 22.0)

            esito_1x2 = "1" if gf_c > gf_t else ("X" if gf_c == gf_t else "2")
            esito_ou25 = "O2.5" if (gf_c + gf_t) > 2.5 else "U2.5"
            esito_gg = "Goal" if (gf_c > 0 and gf_t > 0) else "NoGoal"

            cols_quote = trova_colonne_quote(df)
            quote_reali = {}
            if cols_quote:
                h, d, a = cols_quote
                if pd.notna(riga.get(h)): quote_reali["1"] = float(riga[h])
                if pd.notna(riga.get(d)): quote_reali["X"] = float(riga[d])
                if pd.notna(riga.get(a)): quote_reali["2"] = float(riga[a])

            cols_quote_ou25 = trova_colonne_quote_ou25(df)
            quote_reali_ou = {}
            if cols_quote_ou25:
                over_c, under_c = cols_quote_ou25
                if pd.notna(riga.get(over_c)): quote_reali_ou["O2.5"] = float(riga[over_c])
                if pd.notna(riga.get(under_c)): quote_reali_ou["U2.5"] = float(riga[under_c])

            for mercato, esito_reale in [("1X2", esito_1x2), ("OU25", esito_ou25), ("GGNG", esito_gg)]:
                opzioni = {"1X2": ["1", "X", "2"], "OU25": ["U2.5", "O2.5"],
                           "GGNG": ["Goal", "NoGoal"]}[mercato]
                for opz in opzioni:
                    avvenuto = 1 if opz == esito_reale else 0
                    # Quota reale disponibile per 1X2 e OU25 nei CSV
                    # football-data.co.uk standard (GGNG non ha colonne quote
                    # in questo formato). Quando c'e', calcoliamo anche il P/L
                    # "puntata alla cieca su questa fascia di probabilita',
                    # quota reale, nessun calcolo di edge" -- serve a
                    # rispondere separatamente da "il modello e' ben
                    # calibrato?" alla domanda "avrebbe fatto guadagnare?".
                    if mercato == "1X2":
                        quota_r = quote_reali.get(opz)
                    elif mercato == "OU25":
                        quota_r = quote_reali_ou.get(opz)
                    else:
                        quota_r = None
                    pl_flat_puro = ((quota_r - 1) if avvenuto else -1) if quota_r else None
                    valutazioni.append({
                        "mercato": mercato, "tip": opz,
                        "prob_modello": tips[opz],
                        "avvenuto": avvenuto,
                        "quota_reale": quota_r,
                        "pl_flat_puro": pl_flat_puro,
                    })

            for mercato_e, tips_quote, opzioni_e, esito_e in [
                ("1X2", quote_reali, ["1", "X", "2"], esito_1x2),
                ("OU25", quote_reali_ou, ["U2.5", "O2.5"], esito_ou25),
            ]:
                for tip in opzioni_e:
                    if tip not in tips_quote:
                        continue
                    quota = tips_quote[tip]
                    prob = tips[tip]
                    edge = calcola_edge_pct(prob, quota)
                    if edge > 0 and quota <= QUOTA_CAP:
                        vinta = 1 if tip == esito_e else 0
                        bilancio_flat += (quota - 1) if vinta else -1
                        k = kelly_fraction(prob, quota)
                        puntata_kelly = budget_kelly * k
                        bilancio_kelly += puntata_kelly * ((quota - 1) if vinta else -1)
                        puntate.append({
                            "data": riga["Date"], "match": f"{casa} vs {ospite}",
                            "mercato": mercato_e,
                            "tip": tip, "prob": round(prob, 1), "quota": quota,
                            "edge_pct": round(edge, 1), "vinta": bool(vinta),
                        })

        # aggiorna lo storico (rolling + cumulativo) DOPO aver valutato/scommesso questa partita
        storico[casa]["casa"].append({"gf": gf_c, "gs": gf_t})
        storico[casa]["cum_casa_gf"] += gf_c; storico[casa]["cum_casa_gs"] += gf_t
        storico[casa]["n_casa"] += 1
        storico[ospite]["trasferta"].append({"gf": gf_t, "gs": gf_c})
        storico[ospite]["cum_trasf_gf"] += gf_t; storico[ospite]["cum_trasf_gs"] += gf_c
        storico[ospite]["n_trasf"] += 1

    return pd.DataFrame(valutazioni), pd.DataFrame(puntate), bilancio_flat, bilancio_kelly, budget_kelly


def report_calibrazione(val: pd.DataFrame):
    print("═" * 70)
    print("CALIBRAZIONE (probabilità dichiarata vs frequenza reale osservata)")
    print("═" * 70)
    if val.empty:
        print("Nessuna partita valutata (storico insufficiente per la finestra "
              f"rolling di {FINESTRA_ROLLING} partite — servono più dati/stagioni).")
        return
    val = val.copy()
    val["bin"] = (val["prob_modello"] // 10 * 10).clip(0, 90)
    tab = val.groupby(["mercato", "bin"]).agg(
        n=("avvenuto", "size"),
        prob_media_modello=("prob_modello", "mean"),
        freq_reale=("avvenuto", "mean"),
    ).reset_index()
    tab["freq_reale"] = (tab["freq_reale"] * 100).round(1)
    tab["prob_media_modello"] = tab["prob_media_modello"].round(1)

    # ROI "puntata pura per fascia di probabilita'" (quota reale, NESSUN
    # calcolo di edge -- risponde a "punterei alla cieca sulla fascia X,
    # avrei guadagnato?" separatamente dalla domanda "il modello e' ben
    # calibrato?" sopra). Disponibile solo dove c'e' una quota reale nel
    # CSV (oggi solo 1X2).
    con_quota = val.dropna(subset=["pl_flat_puro"])
    if not con_quota.empty:
        roi_tab = con_quota.groupby(["mercato", "bin"]).agg(
            n_con_quota=("pl_flat_puro", "size"),
            roi_puro_pct=("pl_flat_puro", "mean"),
        ).reset_index()
        roi_tab["roi_puro_pct"] = (roi_tab["roi_puro_pct"] * 100).round(1)
        tab = tab.merge(roi_tab, on=["mercato", "bin"], how="left")

    for mercato in tab["mercato"].unique():
        print(f"\n-- {mercato} --")
        sub = tab[tab["mercato"] == mercato].sort_values("bin")
        colonne = ["bin", "n", "prob_media_modello", "freq_reale"]
        if "roi_puro_pct" in sub.columns:
            colonne += ["n_con_quota", "roi_puro_pct"]
        print(sub[colonne].to_string(index=False))
    if "roi_puro_pct" in tab.columns:
        print("\n'roi_puro_pct' = P/L medio per scommessa (%) puntando FLAT su ogni "
              "partita di quella fascia con la quota reale del CSV, SENZA alcun filtro "
              "di edge -- confrontalo con il ROI sui pick 'edge positivo' qui sotto per "
              "vedere se il filtro edge aiuta o peggiora rispetto a puntare per pura "
              "probabilita'.")

    brier = ((val["prob_modello"] / 100.0 - val["avvenuto"]) ** 2).mean()
    print(f"\nBrier score complessivo (0=perfetto, 0.25=indovinare a caso su binario "
          f"50/50, più basso è meglio): {brier:.4f}")


def report_roi(bets: pd.DataFrame, bilancio_flat: float, bilancio_kelly: float, budget_kelly: float):
    print("\n" + "═" * 70)
    print(f"ROI SUI PICK CON EDGE POSITIVO (1X2 + OU25, quote reali del CSV, quota <= {QUOTA_CAP})")
    print("═" * 70)
    if bets.empty:
        print("Nessuna scommessa con Edge>0 trovata (o quote non disponibili nei CSV).")
        return
    n = len(bets)
    win_rate = bets["vinta"].mean() * 100
    print(f"Scommesse piazzate: {n}  |  Win rate: {win_rate:.1f}%  |  "
          f"Edge medio dichiarato: {bets['edge_pct'].mean():.1f}%")

    if "mercato" in bets.columns:
        for mercato in sorted(bets["mercato"].unique()):
            sub_m = bets[bets["mercato"] == mercato]
            pl_m = sub_m.apply(lambda r: (r["quota"] - 1) if r["vinta"] else -1, axis=1)
            print(f"  {mercato}: {len(sub_m)} scommesse, win rate {sub_m['vinta'].mean()*100:.1f}%, "
                  f"ROI flat {pl_m.mean()*100:+.1f}%")
    print(f"\nStake flat (1 unità a scommessa): P/L = {bilancio_flat:+.2f} unità "
          f"({bilancio_flat / n * 100:+.1f}% ROI per scommessa)")
    print(f"Stake Kelly (8%, bankroll iniziale {budget_kelly:.0f}): "
          f"P/L = {bilancio_kelly:+.2f}  "
          f"({bilancio_kelly / budget_kelly * 100:+.1f}% sul bankroll iniziale)")

    # Dove si concentrano le perdite? Fascia di probabilità dichiarata SOLO
    # sui pick edge-positivo (non su tutte le partite come la calibrazione
    # sopra) -- risponde a "basterebbe alzare la soglia minima di
    # probabilità per salvare il criterio edge, invece di buttarlo via?"
    b = bets.copy()
    b["pl"] = b.apply(lambda r: (r["quota"] - 1) if r["vinta"] else -1, axis=1)
    b["bin"] = (b["prob"] // 10 * 10).clip(0, 90)
    gruppo = ["mercato", "bin"] if "mercato" in b.columns else ["bin"]
    sub = b.groupby(gruppo).agg(
        n=("pl", "size"), win_rate_pct=("vinta", "mean"), roi_pct=("pl", "mean"),
    ).reset_index()
    sub["win_rate_pct"] = (sub["win_rate_pct"] * 100).round(1)
    sub["roi_pct"] = (sub["roi_pct"] * 100).round(1)
    print("\nDettaglio pick edge-positivo per fascia di probabilità dichiarata:")
    print(sub.to_string(index=False))
    for mercato in (sorted(bets["mercato"].unique()) if "mercato" in bets.columns else [None]):
        base = bets[bets["mercato"] == mercato] if mercato else bets
        etichetta = f" ({mercato})" if mercato else ""
        for soglia in (40, 50, 60):
            ristretto = base[base["prob"] >= soglia]
            if ristretto.empty:
                continue
            pl_ristretto = ristretto.apply(lambda r: (r["quota"] - 1) if r["vinta"] else -1, axis=1)
            print(f"  → Solo pick con prob >= {soglia}%{etichetta}: {len(ristretto)} scommesse, "
                  f"win rate {ristretto['vinta'].mean()*100:.1f}%, "
                  f"ROI flat {pl_ristretto.mean()*100:+.1f}%")
    print("\n⚠️  Su un solo campione storico limitato questi numeri sono indicativi, "
          "non una prova statistica — vanno letti come 'il segno è quello giusto?' "
          "più che come rendimento atteso garantito.")


if __name__ == "__main__":
    cartella = sys.argv[1] if len(sys.argv) > 1 else "backtest_data"
    valutazioni, bets, bilancio_flat, bilancio_kelly, budget_kelly = esegui_backtest(cartella)
    report_calibrazione(valutazioni)
    report_roi(bets, bilancio_flat, bilancio_kelly, budget_kelly)
    if not bets.empty:
        out_path = "backtest_risultati.csv"
        bets.to_csv(out_path, index=False)
        print(f"\nDettaglio di ogni scommessa salvato in {out_path}")
