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
