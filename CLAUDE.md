# Matrix Bet V90 — note di progetto

App Streamlit per la generazione e il tracciamento di schedine sportive
(app.py + matrix_leghe.py + matrix_api.py + matrix_modello.py + matrix_db.py).
Usata con soldi reali, quindi ogni modifica va verificata (py_compile,
pyflakes, pytest) prima del commit.

## Vincoli reali di puntata (bet365)

- Puntata minima: **1€**.
- Incrementi ammessi: **multipli di 0,05€** (es. 1.00, 1.05, 1.10, ...).

Da tenere presente in qualsiasi logica futura di sizing/allocazione
percentuale del budget (i campi "Puntata reale (€)" e "Vincita reale
incassata (€)" nello Storico dovranno rispettare questi vincoli quando si
passerà da 1€ fisso a una puntata calcolata in percentuale).

## Deploy

- `git push` non funziona da questo ambiente (nessuna credenziale GitHub) —
  l'utente fa sempre il push da Visual Studio Code.
- Streamlit Cloud a volte mostra ancora codice vecchio dopo un push
  (ImportError su funzioni che in realtà esistono già su GitHub): in quel
  caso serve un "Reboot app" completo da Manage app, non basta aspettare
  il redeploy automatico.

## Metodi di selezione e analisi (ottobre 2026)

- Le schedine giornaliere sono generate con DUE metodi, salvati su Firestore
  col campo `metodo`: **"prob"** (probabilità pura: gambe ordinate per
  probabilità del modello, nessun filtro edge, nessun Kelly, solo quote reali
  bet365; nomi `PROB_SAFETY/PROB_PERFORMANCE/PROB_AZZARDO`) è quello che si
  gioca con soldi veri; **"edge"** (storico, nomi `SAFETY/...`) resta solo come
  confronto/tracking. I record vecchi senza `metodo` sono "edge".
- Pagina nascosta di analisi: `<url-app>/?vista=report_analitico_interno` —
  scarica un JSON con calibrazione per fascia di quota/mercato/lega/numero
  gambe, confronto fra metodi e la **simulazione virtuale** (1€ fisso su ogni
  schedina conclusa dalla prima in memoria, bankroll di prova da 10€).
- Contesto: i dati live (163 gambe) e il backtest (`backtest.py`) non mostrano
  un vantaggio del modello sul bookmaker; nessun tuning della selezione crea
  edge dove non c'è. Prima di cambiare strategia guardare il report, non una
  singola giornata.
