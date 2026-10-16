# Deploy su Firebase (Cloud Run + Hosting) con dominio matrix.mtapp.it

Schema: l'app (Streamlit in un container) gira su **Cloud Run**; **Firebase
Hosting** le sta davanti e serve il dominio `matrix.mtapp.it` (DNS su Aruba, come
mdc.mtapp.it). Il database Firestore resta quello di sempre.

## Prerequisiti (una tantum)
- Progetto Firebase che contiene già il Firestore dell'app, con piano **Blaze**
  (Cloud Run richiede la fatturazione attiva; il consumo di un'app così piccola è
  quasi nullo, ma la carta serve).
- `gcloud` installato (https://cloud.google.com/sdk) e Firebase CLI (`npm i -g firebase-tools`).

## 1. Container su Cloud Run
```
gcloud auth login
gcloud config set project matrix-bet-v90
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
gcloud run deploy matrix-bet --source . --region europe-west1 --allow-unauthenticated ^
  --memory 1Gi --min-instances 0 --max-instances 1 --timeout 3600 --session-affinity ^
  --set-env-vars API_KEY_FOOTBALL=<chiave-api-football>,MATRIX_PASSWORD=<password-scelta>
```
(su PowerShell sostituisci `^` di fine riga con il backtick `` ` ``)
- Credenziali Firestore: nessuna chiave da caricare, l'app usa il service account
  del servizio (di default ha già accesso al Firestore dello stesso progetto).
- `--max-instances 1` + `--session-affinity`: Streamlit tiene lo stato in memoria
  per sessione, con più istanze le sessioni si romperebbero.
- `MATRIX_PASSWORD`: l'app chiede la password prima di mostrare qualsiasi cosa
  (pagina nascosta del report inclusa). Senza questa variabile è aperta a chiunque
  abbia l'indirizzo.

## 2. Firebase Hosting davanti al servizio
```
firebase use matrix-bet-v90
firebase deploy --only hosting
```
Apri l'indirizzo `https://matrix-bet-v90.web.app`.

**Controllo WebSocket (importante):** Streamlit funziona solo con i WebSocket e
non ho potuto verificare che Firebase Hosting li inoltri. Se la pagina resta su
"Please wait…" o dice che la connessione è persa, Hosting non li passa:
in quel caso questa strada non va bene (alternative: server proprio con Docker +
Caddy, oppure mappare il dominio direttamente su Cloud Run, funzione in anteprima).

## 3. Dominio matrix.mtapp.it
Firebase Console → Hosting → *Aggiungi dominio personalizzato* → `matrix.mtapp.it`
→ copia i record DNS che propone (TXT di verifica + A/CNAME) nel DNS di Aruba,
come fatto per gli altri sottodomini. Il certificato SSL lo emette Firebase.
Poi su Aruba togli l'eventuale reindirizzamento di `matrix` creato prima.

## Aggiornare l'app in futuro
`gcloud run deploy matrix-bet --source . --region europe-west1` (stessi parametri
già salvati nel servizio) — niente più "Reboot app".

## Spegnere Streamlit Cloud
Solo dopo aver controllato che su matrix.mtapp.it tutto funzioni (Estrai, Storico,
pagina `?vista=report_analitico_interno`): dashboard Streamlit → app → Delete.
