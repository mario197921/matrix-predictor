// vista-storico.js — "Giocate di oggi" e "Storico Schedine" (port di app.py).
import { S, BUDGET_INIZIALE, esc, fmt, metrica, dettagli, oggiStr, avviso, $, $$ } from './stato.js';
import { getFamily } from './modello.js';
import { eRealeRecord, eSoloPersonaleORealeManuale } from './report.js';
import {
  leggiStorico, aggiornaGiocataReale, aggiornaPuntataReale, aggiornaVincitaReale,
  aggiornaEsitoReale, aggiornaEsitoSchedina, controllaEAggiornaRisultati,
} from './db.js';

const EMOJI_ESITO = { vinta: '✅', persa: '❌', in_attesa: '⏳' };
const CSS_BOX_ESITO = { vinta: 'safety-bg', persa: 'risk-bg', in_attesa: 'performance-bg' };
const NOMI_FAMIGLIA = {
  '1X2': '1X2 (1/X/2/1X/X2/12)', UO: 'Under/Over', MG: 'Multigol', GGNG: 'Goal/NoGoal',
  COMBO: 'Combo (1+Over, ecc.)', RE: 'Risultato Esatto', HTFT: 'HT/FT', PD: 'Pari/Dispari',
  SPECIAL: 'Angoli/Cartellini', ALTRO: 'Altro',
};

const eReale = eRealeRecord;
const eFonteReale = eSoloPersonaleORealeManuale;
const eProposta = r => !eFonteReale(r);
const esitoEff = r => r.esito_reale || r.esito;
const metodoDi = r => r.metodo || 'edge';

function dataOrdinabile(r) {
  const d = r.data ?? '';
  return (d.length === 10 && d[4] === '-' && d[7] === '-' && /^\d{4}$/.test(d.slice(0, 4))) ? d : '0000-00-00';
}
export function storicoOrdinato() {
  return [...S.storico].sort((a, b) => {
    const ka = dataOrdinabile(a), kb = dataOrdinabile(b);
    if (ka !== kb) return ka < kb ? 1 : -1;
    const na = a.nome ?? '', nb = b.nome ?? '';
    return na === nb ? 0 : (na < nb ? 1 : -1);
  });
}

const iconaGamba = eg => eg === 'vinta' ? '✅' : (eg === 'persa' ? '❌' : '⏳');

export function renderGiocateOggi() {
  const box = $('#box-oggi');
  const oggi = oggiStr();
  const giocate = storicoOrdinato().filter(r => r.data === oggi && eReale(r));
  if (!giocate.length) { box.innerHTML = ''; return; }
  const colonne = giocate.map(r => {
    const esito = esitoEff(r) || 'in_attesa';
    const puntata = r.puntata_reale; const quota = r.quota_totale || 0; const vincita = r.vincita_reale;
    const legs = (r.selezioni ?? []).map(s =>
      `<div class="schedina-match" style="margin-bottom:4px;">${iconaGamba(s.esito_gamba)} ${esc(s.match || s.Match || '?')} → <b>${esc(s.tip || s.Tip || '?')}</b></div>`).join('')
      || '<div class="schedina-match">—</div>';
    let info = '';
    if (puntata !== undefined && puntata !== null) {
      if (esito === 'vinta') info = `Puntati ${fmt(puntata)}€ → incassati ${fmt(vincita ?? Math.round(puntata * quota * 100) / 100)}€`;
      else if (esito === 'persa') info = `Puntati ${fmt(puntata)}€ → persi`;
      else info = `Puntati ${fmt(puntata)}€ (in attesa)`;
    }
    return `<div class="strategy-box ${CSS_BOX_ESITO[esito] ?? 'performance-bg'}" style="padding:14px 16px;margin-bottom:12px;">
      <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:1rem;margin-bottom:8px;">${EMOJI_ESITO[esito] ?? '⏳'} ${esc(r.nome ?? '?')}</div>
      ${legs}
      <div style="font-size:0.78rem;color:var(--text2);margin-top:8px;">Quota tot: ${fmt(quota)} · ${esc(info)}</div></div>`;
  });
  box.innerHTML = `<h4>🎯 Giocate di oggi</h4><div class="cols cols-3">${colonne.join('')}</div><hr>`;
}

function metriche(lista, titolo, mostraPnl = false) {
  const esitoDi = mostraPnl ? esitoEff : (r => r.esito);
  const vinte = lista.filter(r => esitoDi(r) === 'vinta').length;
  const perse = lista.filter(r => esitoDi(r) === 'persa').length;
  const attesa = lista.filter(r => !esitoDi(r) || esitoDi(r) === 'in_attesa').length;
  const concluse = vinte + perse;
  let html = `<div><strong>${titolo}</strong><div class="cols cols-4" style="margin-top:6px;">
    ${metrica('✅ Vinte', vinte)}${metrica('❌ Perse', perse)}${metrica('⏳ In attesa', attesa)}
    ${metrica('Win rate', concluse ? (vinte / concluse * 100).toFixed(1) + '%' : '—')}</div>`;
  if (mostraPnl) {
    let puntato = 0; let saldo = 0;
    for (const r of lista) {
      const p = r.puntata_reale;
      if (p === undefined || p === null) continue;
      puntato += p;
      const e = esitoEff(r);
      if (e === 'vinta') saldo += (r.vincita_reale !== undefined && r.vincita_reale !== null) ? r.vincita_reale - p : p * (r.quota_totale || 0) - p;
      else if (e === 'persa') saldo -= p;
    }
    const attuale = BUDGET_INIZIALE + saldo;
    html += `<div style="font-size:0.85rem;margin-top:6px;">💰 Puntato: <b>${fmt(puntato)}€</b> &nbsp;·&nbsp; P&amp;L: <b style="color:${saldo >= 0 ? '#22c55e' : '#ef4444'};">${saldo >= 0 ? '+' : ''}${fmt(saldo)}€</b> &nbsp;·&nbsp; Saldo attuale: <b>${fmt(attuale)}€</b> <span style="color:var(--text2);">(partito da ${fmt(BUDGET_INIZIALE)}€)</span></div>`;
  }
  return html + '</div>';
}

function tabellaFamiglie(ordinato) {
  const st = {};
  for (const r of ordinato) for (const s of r.selezioni ?? []) {
    const tip = s.tip || s.Tip || '';
    if (!tip) continue;
    const fam = getFamily(tip);
    const o = st[fam] ??= { vinte: 0, perse: 0, attesa: 0 };
    if (s.esito_gamba === 'vinta') o.vinte++; else if (s.esito_gamba === 'persa') o.perse++; else o.attesa++;
  }
  const righe = Object.entries(st).map(([fam, o]) => ({ fam, ...o, concluse: o.vinte + o.perse }))
    .sort((a, b) => b.concluse - a.concluse);
  if (!righe.length) return '';
  return `<div style="margin-top:14px;"><strong>📈 Performance per tipo di mercato</strong> (tutte le proposte Matrix, gamba per gamba)
    <div class="tbl-wrap"><table class="tbl"><thead><tr><th>Mercato</th><th>Vinte</th><th>Perse</th><th>In attesa</th><th>Win rate</th></tr></thead><tbody>
    ${righe.map(r => `<tr><td>${esc(NOMI_FAMIGLIA[r.fam] ?? r.fam)}</td><td class="num">${r.vinte}</td><td class="num">${r.perse}</td><td class="num">${r.attesa}</td><td class="num">${r.concluse ? (r.vinte / r.concluse * 100).toFixed(1) + '%' : '—'}</td></tr>`).join('')}
    </tbody></table></div>
    <div class="muted small">Campioni piccoli (poche decine di gambe concluse) vanno letti con cautela — serve accumulare più giorni prima di trarre conclusioni sull'affidabilità di un mercato specifico.</div></div>`;
}

function dettaglioRecord(r) {
  const esito = r.esito || 'in_attesa';
  const eff = r.esito_reale || esito;
  const id = r.doc_id;
  const sel = r.selezioni ?? [];
  let nCorrette = 0; let nValutate = 0;
  const legs = sel.map(s => {
    const eg = s.esito_gamba;
    if (eg === 'vinta' || eg === 'persa') { nValutate++; if (eg === 'vinta') nCorrette++; }
    return `${iconaGamba(eg)} ${esc(s.match || s.Match || '?')} → ${esc(s.tip || s.Tip || '?')}`;
  }).join('<br>');
  const conteggio = nValutate ? ` · ${nCorrette}/${nValutate} corrette` : '';
  const tag = eReale(r) ? '💶 Reale' : (metodoDi(r) === 'prob' ? '🎯 Prob' : '🤖 Matrix');
  const quota = r.quota_totale || 0;
  const nota = r.esito_reale ? ' · 🎯 esito reale diverso dal calcolato' : '';
  const label = `${EMOJI_ESITO[eff] ?? '⏳'} ${esc(r.data ?? '?')} — ${esc(r.nome ?? '?')} · ${tag} · quota ${fmt(quota)}${conteggio}${nota}`;
  const fonteReale = eFonteReale(r);
  const giocata = !!r.giocata_reale;

  let corpo = `<div style="font-size:0.85rem;color:var(--text2);">${legs || '—'}</div>
    <div style="font-size:0.78rem;color:var(--text2);margin-top:4px;">Quota tot: ${fmt(quota)} · Prob. dichiarata: ${fmt((r.probabilita_congiunta || 0) * 100, 1)}% · Budget: ${fmt(r.budget || 0)}€</div>`;

  if (!fonteReale && id) {
    corpo += `<label class="inline-ctl"><input type="checkbox" data-az="giocata" data-id="${esc(id)}"${giocata ? ' checked' : ''}> 💶 L'ho giocata davvero (conta anche nelle statistiche reali)</label>`;
  }
  if (id && (fonteReale || giocata)) {
    const p = r.puntata_reale;
    corpo += `<div class="inline-ctl"><label>💰 Puntata reale (€)</label>
      <input type="number" min="0" step="0.5" id="puntata_${esc(id)}" value="${p !== undefined && p !== null ? p : 1}">
      <button class="btn" data-az="puntata" data-id="${esc(id)}">💾 Salva puntata</button></div>`;
    const er = r.esito_reale || '';
    corpo += `<div class="inline-ctl"><label>🎯 Esito reale (solo se diverso da quello calcolato sul tip Matrix)</label>
      <select id="esitoreale_${esc(id)}" style="width:auto;">
        <option value=""${er === '' ? ' selected' : ''}>Uguale al calcolo automatico</option>
        <option value="vinta"${er === 'vinta' ? ' selected' : ''}>✅ Vinta</option>
        <option value="persa"${er === 'persa' ? ' selected' : ''}>❌ Persa</option></select>
      <button class="btn" data-az="esitoreale" data-id="${esc(id)}">💾 Salva esito reale</button></div>`;
    if (eff === 'vinta') {
      const teorica = Math.round((p ?? 1) * quota * 100) / 100;
      const v = r.vincita_reale;
      corpo += `<div class="inline-ctl"><label>🏆 Vincita reale incassata (€) — bonus bet365 inclusi</label>
        <input type="number" min="0" step="0.5" id="vincita_${esc(id)}" value="${v !== undefined && v !== null ? v : teorica}">
        <button class="btn" data-az="vincita" data-id="${esc(id)}">💾 Salva vincita</button>
        <span class="muted small">Quota teorica Matrix: ${fmt(quota)} → ${fmt(teorica)}€.</span></div>`;
    }
  }
  if (esito === 'in_attesa' && id) {
    corpo += `<div class="inline-ctl"><button class="btn" data-az="esito" data-esito="vinta" data-id="${esc(id)}">✅ Vinta</button>
      <button class="btn" data-az="esito" data-esito="persa" data-id="${esc(id)}">❌ Persa</button></div>`;
  }
  return dettagli(`rec_${id ?? r.nome}`, label, corpo);
}

export function renderStorico() {
  const box = $('#box-storico');
  const ord = storicoOrdinato();
  let corpo = `<div class="inline-ctl"><button class="btn" id="btn-controlla" style="width:auto;">🔄 Controlla risultati partite finite</button><span id="esito-controllo" class="small"></span></div>`;
  if (!S.storico.length) {
    corpo += `<div class="alert alert-warn">Nessuna schedina trovata su Firebase (o la connessione non è raggiungibile).</div>`;
  } else {
    const reale = ord.filter(eReale);
    const matrix = ord.filter(eProposta);
    const prob = matrix.filter(r => metodoDi(r) === 'prob');
    const edge = matrix.filter(r => metodoDi(r) !== 'prob');
    corpo += `<div class="cols cols-2">${metriche(prob, '🎯 Matrix — metodo Probabilità')}${metriche(reale, '💶 Scommesse reali (soldi effettivamente giocati)', true)}</div>
      <div class="cols cols-2" style="margin-top:12px;">${metriche(edge, '🤖 Matrix — metodo Edge (confronto, storico completo)')}</div>
      ${tabellaFamiglie(ord)}<hr>${ord.map(dettaglioRecord).join('')}`;
  }
  box.innerHTML = dettagli('storico', '📊 Storico Schedine', corpo);
}

export async function ricaricaStorico() {
  try { S.storico = await leggiStorico(60); }
  catch (e) { console.error(e); avviso('Errore nella lettura dello storico da Firebase: ' + e.message, 'err'); }
  renderGiocateOggi(); renderStorico();
}

async function conferma(ok) {
  if (ok) await ricaricaStorico(); else avviso('Errore nel salvataggio — controlla la console del browser.', 'err');
}

export function inizializzaStorico() {
  const box = $('#box-storico');
  box.addEventListener('click', async e => {
    const btn = e.target.closest('button');
    if (btn?.id === 'btn-controlla') {
      btn.disabled = true;
      const out = $('#esito-controllo');
      try {
        const r = await controllaEAggiornaRisultati((i, n) => { out.textContent = `Controllo ${i}/${n}…`; });
        await ricaricaStorico();
        const o2 = $('#esito-controllo');
        if (o2) o2.textContent = `✅ ${r.vinte} vinte, ❌ ${r.perse} perse aggiornate. ⏳ ${r.ancora_in_attesa} ancora in attesa. 🔍 ${r.non_valutabili} da verificare a mano.`;
      } catch (err) { avviso('Controllo risultati fallito: ' + err.message, 'err'); btn.disabled = false; }
      return;
    }
    if (!btn?.dataset.az) return;
    const id = btn.dataset.id;
    switch (btn.dataset.az) {
      case 'puntata': return conferma(await aggiornaPuntataReale(id, parseFloat($(`#puntata_${CSS.escape(id)}`).value) || 0));
      case 'vincita': return conferma(await aggiornaVincitaReale(id, parseFloat($(`#vincita_${CSS.escape(id)}`).value) || 0));
      case 'esitoreale': return conferma(await aggiornaEsitoReale(id, $(`#esitoreale_${CSS.escape(id)}`).value || null));
      case 'esito': return conferma(await aggiornaEsitoSchedina(id, btn.dataset.esito));
    }
  });
  box.addEventListener('change', async e => {
    const cb = e.target.closest('input[data-az="giocata"]');
    if (cb) conferma(await aggiornaGiocataReale(cb.dataset.id, cb.checked));
  });
}
