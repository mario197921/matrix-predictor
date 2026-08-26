"""
matrix_leghe.py — Configurazione statica: campionati, livelli di
affidabilità dati, costanti del modello e frequenze medie di mercato.

Nessuna di queste definizioni richiede chiamate di rete: sono tabelle
letterali. La risoluzione a runtime degli ID lega instabili (Norvegia,
coppe nazionali, le tre leghe sudamericane/MLS che collidevano con ID
di altri campionati) resta in app.py perché usa le funzioni API che
vivono in matrix_api.py — qui viene importato e poi mutato in-place lo
stesso dict MASTER_LEAGUES definito sotto.
"""

XG_MAX           = 3.2
XG_MIN           = 0.10
# PERF: analizza_statistiche_avanzate_pro faceva una chiamata
# fixtures/statistics per OGNI partita nelle ultime 10 (fino a 10
# chiamate extra a squadra) solo per possesso/tiri/corner/cartellini.
# I gol (usati per xG casa/trasferta) vengono invece dalla risposta
# /fixtures gia' scaricata, senza chiamate aggiuntive: limitiamo quindi
# le chiamate fixtures/statistics alle ultime N partite, mantenendo
# comunque le ultime 10 per la media gol.
N_PARTITE_STATS_AVANZATE = 5
MARGINE_BK       = 0.93   # ~7% margine bookmaker

# ==========================================
# 🗺️ MASTER LEAGUES — ID VERIFICATI E COMPLETI
# ==========================================
# NOTA sugli ID nordici:
#   Eliteserien NOvegese: l'API restituisce ID 69 come alias ma spesso fallisce.
#   La funzione trova_vero_id_lega() lo risolve a runtime interrogando l'endpoint /leagues.
#   Norwegian First Division (playoff): ID 70
#   Allsvenskan Svezia: 113 (verificato stabile)
#   Superettan Svezia (seconda + playoff): 114
#   Veikkausliiga Finlandia: 244
#   Ykkönen Finlandia (seconda + playoff): 245
#   Superliga Danimarca: 119
#   1. Division Danimarca (playoff): 120

MASTER_LEAGUES = {

    # ── COPPE EUROPEE ──────────────────────────────────────────────
    "🇪🇺 Champions League":           2,
    "🇪🇺 Europa League":              3,
    "🇪🇺 Conference League":          848,

    # ── TOP 5 EUROPEI ──────────────────────────────────────────────
    "🇮🇹 Serie A":                    135,
    "🇮🇹 Serie B":                    136,
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League":           39,
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Championship":             40,
    "🇪🇸 La Liga":                    140,
    "🇩🇪 Bundesliga":                 78,
    "🇫🇷 Ligue 1":                    61,

    # ── SECONDE LINEE EUROPEE ──────────────────────────────────────
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 League One":              41,
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 League Two":              42,
    "🇳🇱 Eerste Divisie":             89,
    "🇩🇪 2. Bundesliga":              79,
    "🇪🇸 La Liga 2":                  141,

    # ── ALTRI CAMPIONATI EUROPEI ───────────────────────────────────
    "🇳🇱 Eredivisie":                 88,
    "🇵🇹 Primeira Liga":              94,
    "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Prem.":           281,
    "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Championship":    284,
    "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish League One":      285,
    "🇹🇷 Süper Lig":                  203,
    "🇧🇪 Pro League":                 144,
    "🇬🇷 Super League":               197,
    "🇨🇭 Super League":               207,
    "🇦🇹 Bundesliga":                 218,
    "🇸🇦 Saudi Pro League":           307,

    # ── NORDICI (Anno solare — stagione=anno corrente) ─────────────
    # ID risolti a runtime da trova_vero_id_lega() per Norvegia.
    # Svezia e Finlandia sono stabili.
    "🇳🇴 Eliteserien":               69,   # → auto-discovery runtime
    "🇳🇴 1. divisjon (Playoff NO)":  70,   # Seconda norvegese + playoff promozione
    "🇸🇪 Allsvenskan":               113,
    "🇸🇪 Superettan (Playoff SE)":   114,  # Seconda svedese + playoff
    "🇫🇮 Veikkausliiga":             244,
    "🇫🇮 Ykkönen (Playoff FI)":      245,  # Seconda finlandese + playoff
    "🇩🇰 Superliga":                 119,
    "🇩🇰 1. Division (Playoff DK)":  120,  # Seconda danese + playoff

    # ── SUDAMERICANI ───────────────────────────────────────────────
    "🇧🇷 Brasileirão Série A":       71,
    "🇧🇷 Brasileirão Série B":       72,
    "🇦🇷 Liga Profesional":          128,
    "🇨🇱 Primera División Chile":    265,
    "🇺🇾 Primera División Uruguay":  268,
    "🇨🇴 Liga BetPlay":              239,
    "🇵🇪 Liga 1 Perù":              281,   # NB: verifica ID con auto-discovery
    "🇪🇨 LigaPro Ecuador":          253,
    "🇧🇴 División Profesional":      349,
    "🇵🇾 División Profesional PY":  239,   # NB: verifica ID con auto-discovery
    "🇻🇪 Liga FUTVE":               232,
    "🇲🇽 Liga MX":                  262,
    "🇺🇸 MLS":                      253,
}

# ==========================================
# 🎯 LIVELLO AFFIDABILITÀ DATI
# ==========================================
# Classifica ogni campionato in base alla profondità dei dati disponibili
# su API-Sports: standings, statistiche avanzate, infortuni, quote reali.
#
# ALTA:  standings + stats avanzate + infortuni + quote reali quasi sempre disponibili
# MEDIA: dati buoni ma con qualche lacuna (es. infortuni parziali, quote non sempre reali)
# BASSA: fallback pesanti attivi (no standings, no infortuni, stats scarse)
LIVELLO_AFFIDABILITA = {
    # ── ALTA — Top 5 Europei + Coppe Europee ────────────────────────────────
    "🇪🇺 Champions League": "ALTA", "🇪🇺 Europa League": "ALTA", "🇪🇺 Conference League": "ALTA",
    "🇮🇹 Serie A": "ALTA", "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": "ALTA", "🇪🇸 La Liga": "ALTA",
    "🇩🇪 Bundesliga": "ALTA", "🇫🇷 Ligue 1": "ALTA",

    # ── MEDIA — Seconde linee Top 5 + campionati europei consolidati ───────
    "🇮🇹 Serie B": "MEDIA", "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Championship": "MEDIA",
    "🇳🇱 Eerste Divisie": "MEDIA", "🇩🇪 2. Bundesliga": "MEDIA", "🇪🇸 La Liga 2": "MEDIA",
    "🇳🇱 Eredivisie": "MEDIA", "🇵🇹 Primeira Liga": "MEDIA",
    "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Prem.": "MEDIA", "🇹🇷 Süper Lig": "MEDIA", "🇧🇪 Pro League": "MEDIA",
    "🇬🇷 Super League": "MEDIA", "🇨🇭 Super League": "MEDIA", "🇦🇹 Bundesliga": "MEDIA",
    "🇸🇦 Saudi Pro League": "MEDIA",
    "🇧🇷 Brasileirão Série A": "MEDIA", "🇦🇷 Liga Profesional": "MEDIA",
    "🇲🇽 Liga MX": "MEDIA", "🇺🇸 MLS": "MEDIA",
    "🇮🇹 Coppa Italia": "MEDIA", "🏴󠁧󠁢󠁥󠁮󠁧󠁿 FA Cup": "MEDIA", "🇪🇸 Copa del Rey": "MEDIA",
    "🇩🇪 DFB Pokal": "MEDIA", "🇫🇷 Coupe de France": "MEDIA",

    # ── BASSA — Leghe minori, playoff, coppe minori, sudamericani minori ───
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 League One": "BASSA", "🏴󠁧󠁢󠁥󠁮󠁧󠁿 League Two": "BASSA",
    "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Championship": "BASSA", "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish League One": "BASSA",
    "🇳🇴 Eliteserien": "BASSA", "🇳🇴 1. divisjon (Playoff NO)": "BASSA",
    "🇸🇪 Allsvenskan": "BASSA", "🇸🇪 Superettan (Playoff SE)": "BASSA",
    "🇫🇮 Veikkausliiga": "BASSA", "🇫🇮 Ykkönen (Playoff FI)": "BASSA",
    "🇩🇰 Superliga": "BASSA", "🇩🇰 1. Division (Playoff DK)": "BASSA",
    "🇧🇷 Brasileirão Série B": "BASSA", "🇨🇱 Primera División Chile": "BASSA",
    "🇺🇾 Primera División Uruguay": "BASSA", "🇨🇴 Liga BetPlay": "BASSA",
    "🇵🇪 Liga 1 Perù": "BASSA", "🇪🇨 LigaPro Ecuador": "BASSA",
    "🇧🇴 División Profesional": "BASSA", "🇵🇾 División Profesional PY": "BASSA",
    "🇻🇪 Liga FUTVE": "BASSA",
    "🇫🇮 Finnish Cup": "BASSA", "🇳🇴 Norwegian Cup": "BASSA",
    "🇸🇪 Svenska Cupen": "BASSA", "🇩🇰 DBU Pokalen": "BASSA",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 EFL Cup": "BASSA", "🇳🇱 KNVB Beker": "BASSA", "🇵🇹 Taça de Portugal": "BASSA",
    "🇧🇪 Croky Cup": "BASSA", "🇹🇷 Türkiye Kupası": "BASSA", "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Cup": "BASSA",
    "🇨🇭 Schweizer Cup": "BASSA", "🇦🇹 ÖFB Cup": "BASSA",
}

AFFIDABILITA_ORDINE = {"ALTA": 3, "MEDIA": 2, "BASSA": 1}
AFFIDABILITA_BADGE = {
    "ALTA":  ("🟢", "#22c55e", "Dati completi"),
    "MEDIA": ("🟡", "#f59e0b", "Dati parziali"),
    "BASSA": ("🔴", "#ef4444", "Dati limitati — stime da momentum"),
}

def get_affidabilita(nome_lega: str) -> str:
    return LIVELLO_AFFIDABILITA.get(nome_lega, "MEDIA")   # default prudente

# Campionati che usano anno solare come stagione
LEGHE_ANNO_SOLARE = {
    "🇳🇴 Eliteserien", "🇳🇴 1. divisjon (Playoff NO)",
    "🇸🇪 Allsvenskan", "🇸🇪 Superettan (Playoff SE)",
    "🇫🇮 Veikkausliiga", "🇫🇮 Ykkönen (Playoff FI)",
    "🇩🇰 Superliga", "🇩🇰 1. Division (Playoff DK)",
    "🇧🇷 Brasileirão Série A", "🇧🇷 Brasileirão Série B",
    "🇦🇷 Liga Profesional",
    "🇨🇱 Primera División Chile", "🇺🇾 Primera División Uruguay",
    "🇨🇴 Liga BetPlay", "🇵🇪 Liga 1 Perù", "🇪🇨 LigaPro Ecuador",
    "🇧🇴 División Profesional", "🇵🇾 División Profesional PY",
    "🇻🇪 Liga FUTVE", "🇲🇽 Liga MX", "🇺🇸 MLS",
}

# Campionati con playoff integrati (standings speciali o gironi multipli)
LEGHE_PLAYOFF = {
    "🇳🇴 1. divisjon (Playoff NO)", "🇸🇪 Superettan (Playoff SE)",
    "🇫🇮 Ykkönen (Playoff FI)", "🇩🇰 1. Division (Playoff DK)",
    "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Championship", "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish League One",
    "🇧🇷 Brasileirão Série B", "🇦🇷 Liga Profesional",
}

COPPE_EUROPEE = {"🇪🇺 Champions League", "🇪🇺 Europa League", "🇪🇺 Conference League"}
LEGHE_CIECHE  = {41, 42}   # League One/Two: radar infortuni offline

# Nomi delle coppe nazionali (i relativi ID vengono risolti a runtime
# in app.py mutando MASTER_LEAGUES, ma l'elenco nomi è statico).
COPPE_NAZIONALI = {
    "🇫🇮 Finnish Cup", "🇳🇴 Norwegian Cup", "🇸🇪 Svenska Cupen", "🇩🇰 DBU Pokalen",
    "🇮🇹 Coppa Italia", "🏴󠁧󠁢󠁥󠁮󠁧󠁿 FA Cup", "🏴󠁧󠁢󠁥󠁮󠁧󠁿 EFL Cup", "🇪🇸 Copa del Rey",
    "🇩🇪 DFB Pokal", "🇫🇷 Coupe de France", "🇳🇱 KNVB Beker",
    "🇵🇹 Taça de Portugal", "🇧🇪 Croky Cup", "🇹🇷 Türkiye Kupası",
    "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Cup", "🇨🇭 Schweizer Cup", "🇦🇹 ÖFB Cup",
}

# Frequenze medie attese per mercato (base statistica europea)
FREQUENZE_MEDIE = {
    'W': 3.0, 'X': 3.5, 'L': 3.0, 'Over': 2.0, 'Goal': 2.2
}

