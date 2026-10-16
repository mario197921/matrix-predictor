// db.js — Persistenza su Firestore (SDK web, compat) delle schedine.
// Port di matrix_db.py. Le regole Firestore consentono l'accesso solo al
// proprietario autenticato con Google.
import { costruisciRecordSchedina, valutaEsitoTip } from './modello.js';
import { scaricaRisultatoPartita } from './api.js';

const COLLEZIONE = 'schedine';
const CAMPI_UTENTE = ['giocata_reale', 'puntata_reale', 'vincita_reale', 'esito_reale'];

function db() { return firebase.firestore(); }

export async function leggiStorico(giorni = 60) {
  const snap = await db().collection(COLLEZIONE).orderBy('data', 'desc').limit(Math.max(1, giorni) * 3).get();
  return snap.docs.map(d => ({ ...d.data(), doc_id: d.id }));
}

const firmaSelezioni = sel => (sel ?? []).map(s => `${s.fixture_id ?? ''}|${s.match}|${s.tip}`).sort().join(';');

// Salva (o aggiorna) una schedina generata. Id documento = data_nome, come
// in Python. Diversamente dalla versione Streamlit NON cancella i dati che
// hai inserito a mano (giocata/puntata/vincita/esito reale) e, se le
// selezioni sono identiche, nemmeno gli esiti già verificati.
export async function salvaSchedina(nome, dataStr, selezioni, qTot, probTot, budget, metodo = 'edge') {
  try {
    const ref = db().collection(COLLEZIONE).doc(`${dataStr}_${nome}`);
    const nuovo = costruisciRecordSchedina(nome, dataStr, selezioni, qTot, probTot, budget, null, metodo);
    const esistente = await ref.get();
    if (esistente.exists) {
      const vecchio = esistente.data();
      for (const c of CAMPI_UTENTE) if (vecchio[c] !== undefined) nuovo[c] = vecchio[c];
      if (vecchio.creato_il) nuovo.creato_il = vecchio.creato_il;
      if (firmaSelezioni(vecchio.selezioni) === firmaSelezioni(nuovo.selezioni)) {
        nuovo.esito = vecchio.esito ?? nuovo.esito;
        nuovo.selezioni = vecchio.selezioni;
      }
    }
    await ref.set(nuovo);
    return true;
  } catch (e) { console.error('[db] salvaSchedina', nome, e); return false; }
}

async function aggiorna(docId, campi) {
  try { await db().collection(COLLEZIONE).doc(docId).update(campi); return true; }
  catch (e) { console.error('[db] aggiorna', docId, e); return false; }
}

export const aggiornaGiocataReale = (id, v) => aggiorna(id, { giocata_reale: !!v });
export const aggiornaPuntataReale = (id, v) => aggiorna(id, { puntata_reale: Number(v) });
export const aggiornaVincitaReale = (id, v) => aggiorna(id, { vincita_reale: Number(v) });
export function aggiornaEsitoReale(id, esito) {
  if (!['vinta', 'persa', null].includes(esito)) return Promise.resolve(false);
  return aggiorna(id, { esito_reale: esito === null ? firebase.firestore.FieldValue.delete() : esito });
}
export function aggiornaEsitoSchedina(id, esito) {
  if (!['vinta', 'persa', 'in_attesa'].includes(esito)) return Promise.resolve(false);
  return aggiorna(id, { esito });
}

// Giocata personale dal carrello (nome PERSONALE_*): come in Python il campo
// "budget" è la cifra indicata; la puntata reale si conferma poi nello Storico.
export const salvaGiocataPersonale = (nome, dataStr, selezioni, qTot, probTot, puntata) =>
  salvaSchedina(nome, dataStr, selezioni, qTot, probTot, puntata, 'edge');

// Controllo automatico dei risultati: stessa logica di Python (una gamba persa
// = schedina persa; esito_gamba salvato non appena noto).
export async function controllaEAggiornaRisultati(onProgresso = () => {}) {
  const riepilogo = { vinte: 0, perse: 0, ancora_in_attesa: 0, non_valutabili: 0 };
  let docs;
  try { docs = (await db().collection(COLLEZIONE).where('esito', '==', 'in_attesa').get()).docs; }
  catch (e) { console.error('[db] lettura in attesa', e); return riepilogo; }

  const cache = new Map();
  const risultato = fid => {
    if (!cache.has(fid)) cache.set(fid, scaricaRisultatoPartita(fid));
    return cache.get(fid);
  };

  let fatte = 0;
  for (const doc of docs) {
    onProgresso(++fatte, docs.length);
    const record = doc.data();
    const selezioni = record.selezioni ?? [];
    if (!selezioni.length) { riepilogo.non_valutabili++; continue; }

    const aggiornate = []; let qualchePersa = false; let qualcheBloccata = false;
    let qualcheInSospeso = false; let cambiato = false;
    for (const sel of selezioni) {
      const egPrec = sel.esito_gamba;
      let egNuovo = (egPrec === 'vinta' || egPrec === 'persa') ? egPrec : null;
      if (egNuovo === null) {
        const fid = sel.fixture_id;
        if (fid === null || fid === undefined) qualcheBloccata = true;
        else {
          const ris = await risultato(fid);
          if (!ris || !ris.finita) qualcheInSospeso = true;
          else {
            const esitoBool = valutaEsitoTip(sel.tip, ris.gcFt, ris.gtFt, ris.gcHt, ris.gtHt);
            if (esitoBool === null) qualcheBloccata = true;
            else egNuovo = esitoBool ? 'vinta' : 'persa';
          }
        }
      }
      if (egNuovo !== (egPrec ?? null)) cambiato = true;
      const agg = { ...sel };
      if (egNuovo !== null) agg.esito_gamba = egNuovo;
      aggiornate.push(agg);
      if (egNuovo === 'persa') qualchePersa = true;
    }

    let esitoFinale;
    if (qualchePersa) esitoFinale = 'persa';
    else if (qualcheInSospeso || qualcheBloccata) esitoFinale = 'in_attesa';
    else esitoFinale = 'vinta';

    if (esitoFinale === 'in_attesa' && !cambiato) {
      if (qualcheBloccata) riepilogo.non_valutabili++; else riepilogo.ancora_in_attesa++;
      continue;
    }
    try {
      await db().collection(COLLEZIONE).doc(doc.id).update({ esito: esitoFinale, selezioni: aggiornate });
      if (esitoFinale === 'vinta') riepilogo.vinte++;
      else if (esitoFinale === 'persa') riepilogo.perse++;
      else if (qualcheBloccata) riepilogo.non_valutabili++;
      else riepilogo.ancora_in_attesa++;
    } catch (e) { console.error('[db] aggiornamento', doc.id, e); riepilogo.ancora_in_attesa++; }
  }
  return riepilogo;
}
