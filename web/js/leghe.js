// GENERATO da matrix_leghe.py — tabelle statiche (campionati, affidabilità, costanti).
export const XG_MAX = 3.2;
export const XG_MIN = 0.1;
export const N_PARTITE_STATS_AVANZATE = 5;
export const MARGINE_BK = 0.93;
// Copia modificabile a runtime (auto-discovery ID), come in Python.
export const MASTER_LEAGUES = {
  "🇪🇺 Champions League": 2,
  "🇪🇺 Europa League": 3,
  "🇪🇺 Conference League": 848,
  "🇮🇹 Serie A": 135,
  "🇮🇹 Serie B": 136,
  "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": 39,
  "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Championship": 40,
  "🇪🇸 La Liga": 140,
  "🇩🇪 Bundesliga": 78,
  "🇫🇷 Ligue 1": 61,
  "🏴󠁧󠁢󠁥󠁮󠁧󠁿 League One": 41,
  "🏴󠁧󠁢󠁥󠁮󠁧󠁿 League Two": 42,
  "🇳🇱 Eerste Divisie": 89,
  "🇩🇪 2. Bundesliga": 79,
  "🇪🇸 La Liga 2": 141,
  "🇳🇱 Eredivisie": 88,
  "🇵🇹 Primeira Liga": 94,
  "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Prem.": 281,
  "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Championship": 284,
  "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish League One": 285,
  "🇹🇷 Süper Lig": 203,
  "🇧🇪 Pro League": 144,
  "🇬🇷 Super League": 197,
  "🇨🇭 Super League": 207,
  "🇦🇹 Bundesliga": 218,
  "🇸🇦 Saudi Pro League": 307,
  "🇳🇴 Eliteserien": 69,
  "🇳🇴 1. divisjon (Playoff NO)": 70,
  "🇸🇪 Allsvenskan": 113,
  "🇸🇪 Superettan (Playoff SE)": 114,
  "🇫🇮 Veikkausliiga": 244,
  "🇫🇮 Ykkönen (Playoff FI)": 245,
  "🇩🇰 Superliga": 119,
  "🇩🇰 1. Division (Playoff DK)": 120,
  "🇧🇷 Brasileirão Série A": 71,
  "🇧🇷 Brasileirão Série B": 72,
  "🇦🇷 Liga Profesional": 128,
  "🇨🇱 Primera División Chile": 265,
  "🇺🇾 Primera División Uruguay": 268,
  "🇨🇴 Liga BetPlay": 239,
  "🇵🇪 Liga 1 Perù": 281,
  "🇪🇨 LigaPro Ecuador": 253,
  "🇧🇴 División Profesional": 349,
  "🇵🇾 División Profesional PY": 239,
  "🇻🇪 Liga FUTVE": 232,
  "🇲🇽 Liga MX": 262,
  "🇺🇸 MLS": 253
};
export const LIVELLO_AFFIDABILITA = {
  "🇪🇺 Champions League": "ALTA",
  "🇪🇺 Europa League": "ALTA",
  "🇪🇺 Conference League": "ALTA",
  "🇮🇹 Serie A": "ALTA",
  "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": "ALTA",
  "🇪🇸 La Liga": "ALTA",
  "🇩🇪 Bundesliga": "ALTA",
  "🇫🇷 Ligue 1": "ALTA",
  "🇮🇹 Serie B": "MEDIA",
  "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Championship": "MEDIA",
  "🇳🇱 Eerste Divisie": "MEDIA",
  "🇩🇪 2. Bundesliga": "MEDIA",
  "🇪🇸 La Liga 2": "MEDIA",
  "🇳🇱 Eredivisie": "MEDIA",
  "🇵🇹 Primeira Liga": "MEDIA",
  "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Prem.": "MEDIA",
  "🇹🇷 Süper Lig": "MEDIA",
  "🇧🇪 Pro League": "MEDIA",
  "🇬🇷 Super League": "MEDIA",
  "🇨🇭 Super League": "MEDIA",
  "🇦🇹 Bundesliga": "MEDIA",
  "🇸🇦 Saudi Pro League": "MEDIA",
  "🇧🇷 Brasileirão Série A": "MEDIA",
  "🇦🇷 Liga Profesional": "MEDIA",
  "🇲🇽 Liga MX": "MEDIA",
  "🇺🇸 MLS": "MEDIA",
  "🇮🇹 Coppa Italia": "MEDIA",
  "🏴󠁧󠁢󠁥󠁮󠁧󠁿 FA Cup": "MEDIA",
  "🇪🇸 Copa del Rey": "MEDIA",
  "🇩🇪 DFB Pokal": "MEDIA",
  "🇫🇷 Coupe de France": "MEDIA",
  "🏴󠁧󠁢󠁥󠁮󠁧󠁿 League One": "BASSA",
  "🏴󠁧󠁢󠁥󠁮󠁧󠁿 League Two": "BASSA",
  "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Championship": "BASSA",
  "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish League One": "BASSA",
  "🇳🇴 Eliteserien": "BASSA",
  "🇳🇴 1. divisjon (Playoff NO)": "BASSA",
  "🇸🇪 Allsvenskan": "BASSA",
  "🇸🇪 Superettan (Playoff SE)": "BASSA",
  "🇫🇮 Veikkausliiga": "BASSA",
  "🇫🇮 Ykkönen (Playoff FI)": "BASSA",
  "🇩🇰 Superliga": "BASSA",
  "🇩🇰 1. Division (Playoff DK)": "BASSA",
  "🇧🇷 Brasileirão Série B": "BASSA",
  "🇨🇱 Primera División Chile": "BASSA",
  "🇺🇾 Primera División Uruguay": "BASSA",
  "🇨🇴 Liga BetPlay": "BASSA",
  "🇵🇪 Liga 1 Perù": "BASSA",
  "🇪🇨 LigaPro Ecuador": "BASSA",
  "🇧🇴 División Profesional": "BASSA",
  "🇵🇾 División Profesional PY": "BASSA",
  "🇻🇪 Liga FUTVE": "BASSA",
  "🇫🇮 Finnish Cup": "BASSA",
  "🇳🇴 Norwegian Cup": "BASSA",
  "🇸🇪 Svenska Cupen": "BASSA",
  "🇩🇰 DBU Pokalen": "BASSA",
  "🏴󠁧󠁢󠁥󠁮󠁧󠁿 EFL Cup": "BASSA",
  "🇳🇱 KNVB Beker": "BASSA",
  "🇵🇹 Taça de Portugal": "BASSA",
  "🇧🇪 Croky Cup": "BASSA",
  "🇹🇷 Türkiye Kupası": "BASSA",
  "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Cup": "BASSA",
  "🇨🇭 Schweizer Cup": "BASSA",
  "🇦🇹 ÖFB Cup": "BASSA"
};
export const AFFIDABILITA_ORDINE = {
  "ALTA": 3,
  "MEDIA": 2,
  "BASSA": 1
};
export const AFFIDABILITA_BADGE = {
  "ALTA": [
    "🟢",
    "#22c55e",
    "Dati completi"
  ],
  "MEDIA": [
    "🟡",
    "#f59e0b",
    "Dati parziali"
  ],
  "BASSA": [
    "🔴",
    "#ef4444",
    "Dati limitati — stime da momentum"
  ]
};
export function getAffidabilita(nome) { return LIVELLO_AFFIDABILITA[nome] ?? 'MEDIA'; }
export const LEGHE_ANNO_SOLARE = new Set([
  "🇦🇷 Liga Profesional",
  "🇧🇴 División Profesional",
  "🇧🇷 Brasileirão Série A",
  "🇧🇷 Brasileirão Série B",
  "🇨🇱 Primera División Chile",
  "🇨🇴 Liga BetPlay",
  "🇩🇰 1. Division (Playoff DK)",
  "🇩🇰 Superliga",
  "🇪🇨 LigaPro Ecuador",
  "🇫🇮 Veikkausliiga",
  "🇫🇮 Ykkönen (Playoff FI)",
  "🇲🇽 Liga MX",
  "🇳🇴 1. divisjon (Playoff NO)",
  "🇳🇴 Eliteserien",
  "🇵🇪 Liga 1 Perù",
  "🇵🇾 División Profesional PY",
  "🇸🇪 Allsvenskan",
  "🇸🇪 Superettan (Playoff SE)",
  "🇺🇸 MLS",
  "🇺🇾 Primera División Uruguay",
  "🇻🇪 Liga FUTVE"
]);
export const LEGHE_PLAYOFF = new Set([
  "🇦🇷 Liga Profesional",
  "🇧🇷 Brasileirão Série B",
  "🇩🇰 1. Division (Playoff DK)",
  "🇫🇮 Ykkönen (Playoff FI)",
  "🇳🇴 1. divisjon (Playoff NO)",
  "🇸🇪 Superettan (Playoff SE)",
  "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Championship",
  "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish League One"
]);
export const COPPE_EUROPEE = new Set([
  "🇪🇺 Champions League",
  "🇪🇺 Conference League",
  "🇪🇺 Europa League"
]);
export const LEGHE_CIECHE = new Set([
  41,
  42
]);
export const COPPE_NAZIONALI = new Set([
  "🇦🇹 ÖFB Cup",
  "🇧🇪 Croky Cup",
  "🇨🇭 Schweizer Cup",
  "🇩🇪 DFB Pokal",
  "🇩🇰 DBU Pokalen",
  "🇪🇸 Copa del Rey",
  "🇫🇮 Finnish Cup",
  "🇫🇷 Coupe de France",
  "🇮🇹 Coppa Italia",
  "🇳🇱 KNVB Beker",
  "🇳🇴 Norwegian Cup",
  "🇵🇹 Taça de Portugal",
  "🇸🇪 Svenska Cupen",
  "🇹🇷 Türkiye Kupası",
  "🏴󠁧󠁢󠁥󠁮󠁧󠁿 EFL Cup",
  "🏴󠁧󠁢󠁥󠁮󠁧󠁿 FA Cup",
  "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Cup"
]);
export const FREQUENZE_MEDIE = {
  "W": 3.0,
  "X": 3.5,
  "L": 3.0,
  "Over": 2.0,
  "Goal": 2.2
};
