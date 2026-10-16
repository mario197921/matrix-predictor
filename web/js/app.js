// app.js — avvio: login Google (solo il proprietario), barra laterale,
// estrazione e collegamento delle viste.
import { S, esc, avviso, $, $$, oggiStr } from './stato.js';
import { MASTER_LEAGUES, AFFIDABILITA_ORDINE, getAffidabilita } from './leghe.js';
import { impostaTokenProvider, getActiveLeagues, svuotaCacheApi, ErroreAutenticazione } from './api.js';
import { inizializzaLeghe, estraiMatrix } from './motore.js';
import { ricaricaStorico, inizializzaStorico } from './vista-storico.js';
import { renderEstrazione, inizializzaEstrazione, aggiornaSchedine, renderCarrello } from './vista-estrazione.js';
import { renderReport } from './vista-report.js';

const EMAIL_AUTORIZZATA = 'mariodt79@gmail.com';
const LIVELLI = [['ALTA', '🟢 ALTA'], ['MEDIA', '🟡 MEDIA'], ['BASSA', '🔴 BASSA']];
const livelliAttivi = new Set(['ALTA', 'MEDIA', 'BASSA']);
let scelte = new Set();
let avviato = false;

const mostra = (id, si) => $(id).classList.toggle('hidden', !si);

function leghePerFiltri() {
  const dict = S.activeLeagues ?? MASTER_LEAGUES;
  return Object.keys(dict).filter(n => livelliAttivi.has(getAffidabilita(n)))
    .sort((a, b) => (AFFIDABILITA_ORDINE[getAffidabilita(b)] ?? 2) - (AFFIDABILITA_ORDINE[getAffidabilita(a)] ?? 2) || (a < b ? -1 : 1));
}

function renderListaLeghe(selezionaTutte = false) {
  const lista = leghePerFiltri();
  if (selezionaTutte) scelte = new Set(lista);
  else scelte = new Set([...scelte].filter(n => lista.includes(n)));
  $('#lista-leghe').innerHTML = lista.map(n =>
    `<label><input type="checkbox" data-lega="${esc(n)}"${scelte.has(n) ? ' checked' : ''}> ${esc(n)}</label>`).join('')
    || '<div class="muted small">Nessun campionato nel livello di affidabilità selezionato.</div>';
  $('#conta-leghe').textContent = `📋 ${scelte.size} campionati selezionati`;
}

function inizializzaSidebar() {
  const oggi = oggiStr();
  $('#data-da').value = oggi; $('#data-a').value = oggi;
  S.start = oggi; S.end = oggi;
  $('#filtro-aff').innerHTML = LIVELLI.map(([k, l]) => `<label><input type="checkbox" data-aff="${k}" checked> ${l}</label>`).join('');
  S.activeLeagues = MASTER_LEAGUES;
  renderListaLeghe(true);

  $('#filtro-aff').addEventListener('change', e => {
    const k = e.target.dataset.aff; if (!k) return;
    if (e.target.checked) livelliAttivi.add(k); else livelliAttivi.delete(k);
    renderListaLeghe(true);
  });
  $('#lista-leghe').addEventListener('change', e => {
    const n = e.target.dataset.lega; if (n === undefined) return;
    if (e.target.checked) scelte.add(n); else scelte.delete(n);
    $('#conta-leghe').textContent = `📋 ${scelte.size} campionati selezionati`;
  });
  $('#sel-tutti').addEventListener('click', e => { e.preventDefault(); renderListaLeghe(true); });
  $('#sel-nessuno').addEventListener('click', e => { e.preventDefault(); scelte = new Set(); renderListaLeghe(); });

  const leggiDate = () => {
    let da = $('#data-da').value || oggiStr(); let a = $('#data-a').value || da;
    if (a < da) [da, a] = [a, da];
    S.start = da; S.end = a;
  };
  $('#data-da').addEventListener('change', leggiDate); $('#data-a').addEventListener('change', leggiDate);

  let timer;
  $('#budget').addEventListener('input', () => {
    S.budgetTotale = Math.max(5, parseFloat($('#budget').value) || 50);
    clearTimeout(timer);
    timer = setTimeout(async () => { if (S.dataMaster.size) { renderCarrello(); await aggiornaSchedine(); } }, 700);
  });

  $('#btn-reset').addEventListener('click', async () => {
    svuotaCacheApi();
    S.dataMaster = new Map(); S.allTips = []; S.carrello = new Map();
    await renderEstrazione();
    avviso('✅ Cache svuotata!', 'ok');
  });

  $('#btn-scan').addEventListener('click', async e => {
    leggiDate();
    const b = e.target; b.disabled = true; b.textContent = '⏳ Scansione…';
    try {
      S.activeLeagues = await getActiveLeagues(S.start, S.end, MASTER_LEAGUES);
      if (!Object.keys(S.activeLeagues).length) avviso('Nessun campionato supportato attivo.');
      renderListaLeghe(true);
    } catch (err) { avviso('Scansione fallita: ' + err.message, 'err'); }
    b.disabled = false; b.textContent = '🔍 Scansiona';
  });

  $('#btn-genera').addEventListener('click', async e => {
    leggiDate();
    S.budgetTotale = Math.max(5, parseFloat($('#budget').value) || 50);
    if (!scelte.size) return avviso('Seleziona almeno un campionato.');
    const b = e.target; b.disabled = true;
    const prog = $('#progresso'); prog.classList.remove('hidden');
    const setProg = (i, n, nome) => {
      $('.progress-bar', prog).style.width = `${(i / n) * 100}%`;
      $('.progress-txt', prog).textContent = `Analisi V90: ${nome} (${i}/${n})`;
    };
    try {
      const ordine = leghePerFiltri().filter(n => scelte.has(n));
      const r = await estraiMatrix({
        scelte: ordine, activeDict: S.activeLeagues ?? MASTER_LEAGUES, startStr: S.start, endStr: S.end,
        onProgresso: setProg, onAvviso: t => avviso(t),
      });
      S.dataMaster = r.dataMaster; S.allTips = r.allTips; S.carrello = new Map();
      if (!S.dataMaster.size) avviso('Nessuna partita trovata per i campionati e il periodo selezionati.');
      await renderEstrazione();
    } catch (err) {
      if (err instanceof ErroreAutenticazione) { avviso(err.message, 'err'); await firebase.auth().signOut(); }
      else { console.error(err); avviso('Errore durante l’estrazione: ' + err.message, 'err'); }
    }
    prog.classList.add('hidden'); b.disabled = false;
  });

  $('#btn-esci').addEventListener('click', e => { e.preventDefault(); firebase.auth().signOut(); });
}

async function avvia(user) {
  mostra('#login', false); mostra('#app', true);
  $('#utente').textContent = user.email;
  const soloReport = new URLSearchParams(location.search).get('vista') === 'report_analitico_interno';
  mostra('#sidebar', !soloReport);
  mostra('#vista-principale', !soloReport); mostra('#vista-report', soloReport);
  if (soloReport) { await renderReport(); return; }
  if (avviato) { await ricaricaStorico(); return; }
  avviato = true;
  const caricamento = avviso('Inizializzazione campionati…', 'ok');
  try { await inizializzaLeghe(); }
  catch (e) { console.error(e); avviso('Auto-discovery campionati non riuscita: ' + e.message, 'warn'); }
  caricamento.remove();
  inizializzaSidebar(); inizializzaStorico(); inizializzaEstrazione();
  await ricaricaStorico();
}

document.addEventListener('DOMContentLoaded', () => {
  if (typeof firebase === 'undefined' || !firebase.apps?.length) {
    mostra('#login', true);
    $('#login-msg').textContent = 'Firebase non inizializzato: apri il sito dall’indirizzo Firebase Hosting (https://…web.app o matrix.mtapp.it).';
    return;
  }
  impostaTokenProvider(async () => firebase.auth().currentUser?.getIdToken());
  $('#btn-login').addEventListener('click', async () => {
    $('#login-msg').textContent = '';
    try { await firebase.auth().signInWithPopup(new firebase.auth.GoogleAuthProvider()); }
    catch (e) { $('#login-msg').textContent = 'Accesso non riuscito: ' + e.message; }
  });
  firebase.auth().onAuthStateChanged(async user => {
    if (!user) { mostra('#app', false); mostra('#login', true); return; }
    if (user.email !== EMAIL_AUTORIZZATA || !user.emailVerified) {
      $('#login-msg').textContent = 'Account non autorizzato.';
      await firebase.auth().signOut(); return;
    }
    await avvia(user);
  });
});
