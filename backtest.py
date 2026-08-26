"""
backtest.py — Backtest storico del motore Poisson/Kelly di Matrix Bet V90
contro risultati reali (CSV gratuiti da football-data.co.uk).

COSA TESTA E COSA NO (leggi prima di interpretare i risultati)
----------------------------------------------------------------
Questo script usa le STESSE funzioni di produzione di matrix_modello.py
(calcola_tutti_i_mercati, get_quota_finale, calcola_edge_pct,
kelly_fraction) — non una riscrittura — quindi il motore Poisson/Kelly
testato qui è esattamente quello che gira nell'app.

Lo xG in ingresso, però, è un PROXY semplificato: usa solo la media
gol fatti/subiti in casa/trasferta delle ultime N partite di ciascuna
squadra (la stessa formula "momentum" di app.py, xg = sqrt(gf * gs
avversario)), calcolata esclusivamente sui dati storici del CSV, PRIMA
della partita in esame (nessun look-ahead). Non include: infortuni,
H2H, motivazione/pressione, meteo, arbitro, correttivi di lega — tutta
la parte che nell'app vive nel loop principale e richiede l'API live.

Quindi: un risultato positivo qui dice "il motore Poisson di base +
il momentum xG sono ragionevolmente calibrati e non distruggono valore
nel tempo". NON dice "l'app intera, con tutti i correttivi, è
profittevole" — quello richiederebbe rigiocare l'intera pipeline con
dati storici di infortuni/quote/H2H, che l'API non fornisce per il
passato in un formato comodo da backtestare.

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
QUOTE_COLONNE_PRIORITA = [
    ("B365H", "B365D", "B365A"),
    ("BWH", "BWD", "BWA"),
    ("IWH", "IWD", "IWA"),
    ("PSH", "PSD", "PSA"),
    ("AvgH", "AvgD", "AvgA"),
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


def xg_momentum(storico_squadra: dict, casa: str, ospite: str):
    """Replica la formula 'momentum' di app.py: xg = sqrt(gf_lato * gs_lato_avversario),
    usando SOLO le partite già viste (nessun look-ahead)."""
    def media(dq, chiave):
        vals = [m[chiave] for m in dq]
        return sum(vals) / len(vals) if vals else None

    dq_casa = storico_squadra[casa]["casa"]
    dq_osp  = storico_squadra[ospite]["trasferta"]
    if len(dq_casa) < FINESTRA_ROLLING or len(dq_osp) < FINESTRA_ROLLING:
        return None, None   # warm-up insufficiente

    gf_home_c = media(dq_casa, "gf")
    gs_home_c = media(dq_casa, "gs")
    gf_away_t = media(dq_osp, "gf")
    gs_away_t = media(dq_osp, "gs")

    xg_c = math.sqrt(max(0.01, gf_home_c) * max(0.01, gs_away_t))
    xg_t = math.sqrt(max(0.01, gf_away_t) * max(0.01, gs_home_c))
    xg_c = min(XG_MAX, max(XG_MIN, xg_c))
    xg_t = min(XG_MAX, max(XG_MIN, xg_t))
    return xg_c, xg_t


def esegui_backtest(cartella: str):
    df = carica_csv(cartella)
    print(f"Caricate {len(df)} partite da {df['__file__'].nunique()} file "
          f"({df['Date'].min().date()} → {df['Date'].max().date()})\n")

    storico = defaultdict(lambda: {"casa": deque(maxlen=FINESTRA_ROLLING),
                                    "trasferta": deque(maxlen=FINESTRA_ROLLING)})

    valutazioni = []   # una riga per (partita, mercato valutato)
    bilancio_flat = bilancio_kelly = 0.0
    budget_kelly = 100.0   # unità di bankroll iniziale per il simulatore Kelly
    puntate = []

    for _, riga in df.iterrows():
        casa = semplifica_nome(str(riga["HomeTeam"]))
        ospite = semplifica_nome(str(riga["AwayTeam"]))
        gf_c, gf_t = int(riga["FTHG"]), int(riga["FTAG"])

        xg_c, xg_t = xg_momentum(storico, casa, ospite)
        if xg_c is not None:
            tips = calcola_tutti_i_mercati(xg_c, xg_t, 9.0, 4.0, False, 22.0)

            esito_1x2 = "1" if gf_c > gf_t else ("X" if gf_c == gf_t else "2")
            esito_ou25 = "O2.5" if (gf_c + gf_t) > 2.5 else "U2.5"
            esito_gg = "Goal" if (gf_c > 0 and gf_t > 0) else "NoGoal"

            for mercato, esito_reale in [("1X2", esito_1x2), ("OU25", esito_ou25), ("GGNG", esito_gg)]:
                opzioni = {"1X2": ["1", "X", "2"], "OU25": ["U2.5", "O2.5"],
                           "GGNG": ["Goal", "NoGoal"]}[mercato]
                for opz in opzioni:
                    valutazioni.append({
                        "mercato": mercato, "tip": opz,
                        "prob_modello": tips[opz],
                        "avvenuto": 1 if opz == esito_reale else 0,
                    })

            cols_quote = trova_colonne_quote(df)
            if cols_quote:
                h, d, a = cols_quote
                quote_reali = {}
                if pd.notna(riga.get(h)): quote_reali["1"] = float(riga[h])
                if pd.notna(riga.get(d)): quote_reali["X"] = float(riga[d])
                if pd.notna(riga.get(a)): quote_reali["2"] = float(riga[a])
                for tip in ["1", "X", "2"]:
                    if tip not in quote_reali:
                        continue
                    quota = quote_reali[tip]
                    prob = tips[tip]
                    edge = calcola_edge_pct(prob, quota)
                    if edge > 0:
                        vinta = 1 if tip == esito_1x2 else 0
                        bilancio_flat += (quota - 1) if vinta else -1
                        k = kelly_fraction(prob, quota)
                        puntata_kelly = budget_kelly * k
                        bilancio_kelly += puntata_kelly * ((quota - 1) if vinta else -1)
                        puntate.append({
                            "data": riga["Date"], "match": f"{casa} vs {ospite}",
                            "tip": tip, "prob": round(prob, 1), "quota": quota,
                            "edge_pct": round(edge, 1), "vinta": bool(vinta),
                        })

        # aggiorna lo storico DOPO aver valutato/scommesso questa partita
        storico[casa]["casa"].append({"gf": gf_c, "gs": gf_t})
        storico[ospite]["trasferta"].append({"gf": gf_t, "gs": gf_c})

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
    for mercato in tab["mercato"].unique():
        print(f"\n-- {mercato} --")
        sub = tab[tab["mercato"] == mercato].sort_values("bin")
        print(sub[["bin", "n", "prob_media_modello", "freq_reale"]].to_string(index=False))

    brier = ((val["prob_modello"] / 100.0 - val["avvenuto"]) ** 2).mean()
    print(f"\nBrier score complessivo (0=perfetto, 0.25=indovinare a caso su binario "
          f"50/50, più basso è meglio): {brier:.4f}")


def report_roi(bets: pd.DataFrame, bilancio_flat: float, bilancio_kelly: float, budget_kelly: float):
    print("\n" + "═" * 70)
    print("ROI SUI PICK CON EDGE POSITIVO (1X2, quote reali del CSV)")
    print("═" * 70)
    if bets.empty:
        print("Nessuna scommessa con Edge>0 trovata (o quote non disponibili nei CSV).")
        return
    n = len(bets)
    win_rate = bets["vinta"].mean() * 100
    print(f"Scommesse piazzate: {n}  |  Win rate: {win_rate:.1f}%  |  "
          f"Edge medio dichiarato: {bets['edge_pct'].mean():.1f}%")
    print(f"\nStake flat (1 unità a scommessa): P/L = {bilancio_flat:+.2f} unità "
          f"({bilancio_flat / n * 100:+.1f}% ROI per scommessa)")
    print(f"Stake Kelly (25%, bankroll iniziale {budget_kelly:.0f}): "
          f"P/L = {bilancio_kelly:+.2f}  "
          f"({bilancio_kelly / budget_kelly * 100:+.1f}% sul bankroll iniziale)")
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
