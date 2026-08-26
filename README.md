# matrix# 🎯 Matrix Bet V90

Sistema di analisi predittiva per scommesse calcistiche basato su **Streamlit** e **API-Sports**.

## ✨ Funzionalità

- 📡 Dati live da [API-Football (api-sports.io)](https://www.api-sports.io/)
- 🌍 Supporto **FIFA World Cup 2026** con logica dedicata per nazionali
- 🇳🇴 Campionati nordici (anno solare) con auto-discovery ID corretto
- ⚡ Gestione **playoff** per tutte le leghe che li prevedono
- 🌎 Campionati sudamericani (Brasileirão, Liga Profesional, ecc.)
- 📊 Calcolo xG con modello Poisson + correttivi (infortuni, H2H, meteo, motivazione)
- 💰 **Value Bet Index** (Edge%) e **Kelly Criterion** per il sizing delle puntate
- 🏗️ Bet Builder interattivo + generatore automatico di 3 schedine (Safety / Performance / Azzardo)

---

## 🚀 Installazione locale

### 1. Clona il repository
```bash
git clone https://github.com/tuo-utente/matrix-bet-v90.git
cd matrix-bet-v90
```

### 2. Crea un ambiente virtuale
```bash
python -m venv venv
source venv/bin/activate      # macOS / Linux
venv\Scripts\activate         # Windows
```

### 3. Installa le dipendenze
```bash
pip install -r requirements.txt
```

### 4. Configura la API Key

Copia il file di esempio e inserisci la tua chiave:
```bash
cp .env.example .env
```
Apri `.env` e sostituisci il valore placeholder:
```
API_KEY_FOOTBALL=la_tua_chiave_reale
```
> ⚠️ **Non committare mai il file `.env`** — è già escluso da `.gitignore`.

### 5. Avvia l'app
```bash
streamlit run matrix_bet_v90.py
```

---

## ☁️ Deploy su Streamlit Cloud

1. Fai il fork/push del repo su GitHub (senza il file `.env`)
2. Vai su [share.streamlit.io](https://share.streamlit.io) e collega il repo
3. In **Settings → Secrets**, aggiungi:
```toml
API_KEY_FOOTBALL = "la_tua_chiave_reale"
```
4. Deploy — la chiave viene letta automaticamente da `st.secrets`

---

## 📁 Struttura del progetto

```
matrix-bet-v90/
│
├── matrix_bet_v90.py      # App principale
├── requirements.txt       # Dipendenze Python
├── .env.example           # Template variabili d'ambiente (sicuro da committare)
├── .gitignore             # Esclude .env, cache, ecc.
└── README.md              # Questo file
```

---

## ⚙️ Campionati supportati

| Area | Campionati |
|---|---|
| 🌍 Mondiale | FIFA World Cup 2026 |
| 🇪🇺 Coppe EU | Champions League, Europa League, Conference League |
| 🇮🇹🏴󠁧󠁢󠁥󠁮󠁧󠁿🇪🇸🇩🇪🇫🇷 | Top 5 + seconde divisioni |
| 🇳🇴🇸🇪🇫🇮🇩🇰 | Campionati nordici + seconde divisioni + playoff |
| 🇧🇷🇦🇷🇨🇱🇨🇴 | Sudamericani |
| 🇸🇦🇹🇷🇧🇪🇳🇱🇵🇹 | Altri campionati europei |

---

## 📋 Limiti API

Il piano standard di API-Sports prevede **7.500 chiamate/giorno**.  
Stima per sessione tipica:
- Infrasettimanale (nordici/coppe): ~500–800 chiamate
- Weekend (tutti i campionati): ~2.500–3.000 chiamate
- Mondiale (fase a gironi): ~400–600 chiamate per giornata

La cache integrata (`@st.cache_data`) riduce le chiamate di circa l'80% nelle sessioni successive.

---

## ⚠️ Disclaimer

Questo strumento è sviluppato a **scopo analitico e informativo**.  
Le previsioni non garantiscono risultati. Scommetti responsabilmente.
-predictor