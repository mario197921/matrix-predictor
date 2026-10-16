# Matrix Bet su matrix.mtapp.it (Firebase, senza Python)

Struttura: sito statico in `web/` (HTML/CSS/JS) su Firebase Hosting + una piccola
Cloud Function Node (`functions/`) che custodisce la chiave API-Football +
Firestore (le schedine). Login Google, solo `mariodt79@gmail.com`.

## 1. Console Firebase (progetto `matrix-bet-v90`)
1. **Impostazioni progetto → Le tue app → Aggiungi app Web** (se non c'è già): serve perché Hosting fornisca la configurazione (`/__/firebase/init.js`).
2. **Authentication → Metodo di accesso → Google → Abilita.**
3. **Passa al piano Blaze** (necessario per le Cloud Functions; con questo uso il costo è trascurabile).

## 2. Dal terminale, nella cartella del progetto
```
npm install -g firebase-tools
firebase login
firebase use matrix-bet-v90
firebase functions:secrets:set API_KEY_FOOTBALL     (incolla la chiave API-Football)
cd functions && npm install && cd ..
firebase deploy
```
`firebase deploy` pubblica sito, funzione e regole Firestore (`firestore.rules`:
solo il tuo account Google; il vecchio accesso Streamlit con service account non
è toccato dalle regole).

Prova subito su `https://matrix-bet-v90.web.app`.

## 3. Dominio matrix.mtapp.it
Firebase Console → Hosting → **Aggiungi dominio personalizzato** → `matrix.mtapp.it`,
poi crea in Aruba i record DNS che Firebase indica (TXT di verifica + A/AAAA o CNAME),
come per le altre app. Se il login Google dà "dominio non autorizzato":
Authentication → Impostazioni → Domini autorizzati → aggiungi `matrix.mtapp.it`.

## 4. Pagina report nascosta
`https://matrix.mtapp.it/?vista=report_analitico_interno` (dopo il login):
simulazione bankroll virtuale + JSON scaricabile.

## 5. Dopo che funziona
Spegni l'app su Streamlit Cloud. I file Python (`app.py`, `matrix_*.py`,
`backtest.py`, test) non servono più al sito: si possono archiviare/eliminare.

## Test (opzionale)
`npm test` esegue i test JS, che confrontano il modello JS con i risultati del
modello Python (`tests_js/golden.json`, rigenerabile con `python tests_js/gen_golden.py`).
