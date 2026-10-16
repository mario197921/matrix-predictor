// vista-estrazione.js — le 3 schede dopo l'estrazione (port di app.py):
// 1) Top 10 & Builder, 2) Esploratore partite, 3) Schedine automatiche.
import { S, esc, htmlSicuro, fmt, sgn, metrica, dettagli, oggiStr, avviso, scaricaFile, timestampFile, $, $$ } from './stato.js';
import { AFFIDABILITA_BADGE, AFFIDABILITA_ORDINE, COPPE_EUROPEE, getAffidabilita } from './leghe.js';
import {
  calcolaEdgePct, kellyFraction, getQuotaFinale, costruisciSchedinaDinamica,
} from './modello.js';
import { salvaSchedina, salvaGiocataPersonale } from './db.js';
import { ricaricaStorico } from './vista-storico.js';

const chiaveSel = x => `${x.Match}_${x.Tip}`;

// ═══════════════ TAB 1 — TOP 10 & BUILDER ═══════════════
function tabellaTop(id, titolo, filtro, minQ, maxQ, sortBy, soloEdgePos = true) {
  const pool = S.allTips.filter(x => filtro(x.Tip) && Number(x.Quota) >= minQ && Number(x.Quota) <= maxQ
    && (soloEdgePos ? Number(x.Edge ?? 0) > 0 : true));
  let corpo;
  if (!pool.length) corpo = '<div class="alert">Nessun dato per questa categoria.</div>';
  else {
    const righe = [...pool].sort((a, b) => b[sortBy] - a[sortBy]).slice(0, 10);
    corpo = `<div class="tbl-wrap"><table class="tbl"><thead><tr><th>Seleziona</th><th>Match</th><th>Tip</th><th>Probabilità (%)</th><th>Quota</th><th>Edge (%)</th><th>Kelly (%)</th><th>Time</th><th>League</th><th>Dati</th></tr></thead><tbody>
      ${righe.map(x => {
        S.righeTabella.set(chiaveSel(x), x);
        return `<tr><td><input type="checkbox" data-cart="${esc(chiaveSel(x))}" data-src="tab"${S.carrello.has(chiaveSel(x)) ? ' checked' : ''}></td>
        <td>${esc(x.Match)}</td><td><b>${esc(x.Tip)}</b></td><td class="num">${fmt(x.Prob, 1)}%</td><td class="num">${fmt(x.Quota)}</td>
        <td class="num">${fmt(x.Edge, 1)}%</td><td class="num">${fmt(x.Kelly * 100, 1)}%</td><td>${esc(x.Time)}</td><td>${esc(x.League)}</td>
        <td>${AFFIDABILITA_BADGE[x.Aff][0]}</td></tr>`;
      }).join('')}</tbody></table></div>`;
  }
  return `<h3>${titolo}</h3>${corpo}`;
}

function renderTab1() {
  S.righeTabella = new Map();
  for (const t of S.allTips) t.Score = t.Edge > 0 ? (t.Prob / 100.0) * Math.max(0, t.Edge) : 0.0;
  const parti = [
    tabellaTop('t1a', '👑 Top 10 Value Bet Assoluta (1.05–1.50)', t => !['U4.5', 'Casa O0.5', 'Ospite O0.5'].includes(t), 1.10, 1.50, 'Score'),
    tabellaTop('t1b', '🛡️ Top 10 Doppie Chance (1.05–1.80)', t => ['1X', 'X2', '12'].includes(t), 1.10, 1.80, 'Score'),
    tabellaTop('t1c', '⚽ Top 10 Over / Under (1.05–2.00)', t => (t.startsWith('O') || t.startsWith('U')) && !t.includes('+'), 1.10, 2.00, 'Score'),
    tabellaTop('t1d', '🎯 Top 10 Goal / NoGoal (1.05–2.00)', t => ['Goal', 'NoGoal'].includes(t), 1.10, 2.00, 'Score'),
    tabellaTop('t1e', '🥅 Top 10 Multigol (1.05–2.00)', t => t.startsWith('MG'), 1.10, 2.00, 'Score'),
    tabellaTop('t1f', '🧩 Top 10 Combo Match (1.05–2.50)', t => t.includes('+'), 1.10, 2.50, 'Score'),
    tabellaTop('t1g', '🧨 Top 10 Azzardi (Quote 2.50–5.00)', () => true, 2.50, 5.00, 'Edge', false),
  ];
  return `<h2>🛒 BET BUILDER &amp; CLASSIFICHE OMNI-MARKET</h2>
    <div class="muted small">💡 Edge% = valore atteso · Kelly% = puntata suggerita (su quote basse può dare 0%).</div>
    ${parti.join('')}<hr><div class="strategy-box builder-bg" id="carrello-box"></div>`;
}

export function renderCarrello() {
  const box = $('#carrello-box');
  if (!box) return;
  const carrello = [...S.carrello.values()];
  let html = '<h2>🧾 IL TUO CARRELLO</h2>';
  if (!carrello.length) html += '<div class="alert">👆 Spunta qualche voce dalle classifiche per costruire la schedina.</div>';
  else {
    let qTot = 1.0; let probTot = 1.0; let txt = '=== RICEVUTA MATRIX V90 ===\n\n';
    for (const p of carrello) {
      const edge = p.Edge ?? 0; const kelly = p.Kelly ?? 0;
      html += `<div class="schedina-row"><div><div style="font-weight:600;color:var(--text);">✅ ${esc(p.Match)} → <strong>${esc(p.Tip)}</strong></div>
        <div class="schedina-match">${esc(p.League ?? '')} | ${esc(p.Time)}</div></div>
        <div style="text-align:right;"><span class="${p.Real ? 'quota-real' : 'quota-calc'}">Q ${fmt(p.Quota)}</span>
        <span class="${edge > 0 ? 'edge-positive' : 'edge-negative'}">${sgn(edge, 1)}%</span>
        <span class="kelly-pill">K: ${fmt(kelly * 100, 1)}%</span></div></div>`;
      qTot *= Number(p.Quota); probTot *= Number(p.Prob) / 100.0;
      txt += `[${p.Time}] ${p.Match} -> ${p.Tip} @ ${fmt(p.Quota)} | Edge: ${fmt(edge, 1)}%\n`;
    }
    const b = S.budgetTotale;
    txt += `\n📊 QUOTA TOTALE: ${fmt(qTot)}\n🎯 PROBABILITÀ CONGIUNTA: ${fmt(probTot * 100)}%\n💰 VINCITA STIMATA (su ${b}€): ~${fmt(b * qTot)}€\n`;
    S.testoCarrello = txt; S.carrelloTot = { qTot, probTot };
    html += `<div class="cols cols-3" style="margin-top:12px;">${metrica('Quota Totale', fmt(qTot))}${metrica('Prob. Congiunta', fmt(probTot * 100) + '%')}${metrica(`Vincita (${b}€)`, '~' + fmt(b * qTot) + '€')}</div>
      <div class="inline-ctl"><button class="btn" data-az="scarica-carrello">💾 SCARICA SCHEDINA (TXT)</button></div>
      <div class="inline-ctl"><label>Quanto punti su questa schedina (€):</label>
        <input type="number" id="stake-personale" min="0.5" step="0.5" value="10">
        <button class="btn" data-az="salva-personale">🗂️ Salva questa schedina come giocata personale</button></div>`;
  }
  box.innerHTML = html;
}

function sincronizzaCheckbox() {
  for (const cb of $$('input[data-cart]')) cb.checked = S.carrello.has(cb.dataset.cart);
}

// ═══════════════ TAB 2 — ESPLORATORE ═══════════════
function schedaSquadra(nome, rank, xg, forma, stan, count, t1, sq, gkOut, defOut, stile, poss, par, conv, cs, fts, icona, camp) {
  const casa = icona === '🏠';
  const rankLbl = COPPE_EUROPEE.has(camp) ? '' : `<span style="font-size:0.7rem;color:var(--text2);margin-left:6px;">#${rank}</span>`;
  const formaHtml = (forma || '').split('').map(ch => `<span class="form-char ${ch === 'W' ? 'form-W' : (ch === 'D' ? 'form-D' : 'form-L')}">${esc(ch)}</span>`).join('');
  let badge = '';
  if (t1 > 0) badge += `<span class="tag tag-rosso">⭐ ${t1} Star out</span>`;
  if (sq > 0) badge += `<span class="tag tag-rosso">🟥 ${sq} Squalif.</span>`;
  if (gkOut) badge += '<span class="tag tag-rosso">🧤 PO out</span>';
  if (defOut >= 2) badge += '<span class="tag tag-rosso">🧱 2+ Dif. out</span>';
  const assenti = badge || (count === 0 ? '<span class="tag tag-verde">✅ Rosa al completo</span>' : `<span class="tag tag-giallo">🚑 ${count} assenti</span>`);
  const xgPct = Math.min(100, Math.floor((xg / 3.2) * 100));
  const fatica = stan.includes('Fatigue') ? '⚠️ Fatigue' : '✅ Riposo';
  return `<div class="team-panel ${casa ? 'team-panel-home' : 'team-panel-away'}">
    <div class="team-panel-shine"></div>
    <div class="team-name">${icona} ${esc(nome)} ${rankLbl}</div>
    <div class="${casa ? 'xg-home' : 'xg-away'} xg-number">xG ${fmt(xg)}</div>
    <div class="xg-bar-wrap"><div class="xg-bar-fill ${casa ? 'xg-bar-home' : 'xg-bar-away'}" style="width:${xgPct}%"></div></div>
    <div style="margin-bottom:8px;">${formaHtml}<span style="font-size:0.72rem;color:var(--text2);margin-left:8px;">${fatica}</span></div>
    <div style="margin-bottom:10px;">${assenti}</div>
    <div class="divider"></div>
    <div class="stat-row"><span class="stat-label">Stile di gioco</span><span class="stat-value">${esc(stile)}</span></div>
    <div class="stat-row"><span class="stat-label">Possesso medio</span><span class="stat-value">${fmt(poss, 0)}%</span></div>
    <div class="stat-row"><span class="stat-label">Parate / gara</span><span class="stat-value">${fmt(par, 1)}</span></div>
    <div class="stat-row"><span class="stat-label">Cinismo (da gioco)</span><span class="stat-value">1 gol / ${fmt(conv, 1)} tiri</span></div>
    <div class="stat-row"><span class="stat-label">Clean Sheet</span><span class="stat-value" style="color:var(--green)">${fmt(cs, 0)}%</span></div>
    <div class="stat-row" style="border:none"><span class="stat-label">A Secco</span><span class="stat-value" style="color:var(--red)">${fmt(fts, 0)}%</span></div></div>`;
}

function renderRitardi(lista, label) {
  if (!lista.length) return `<div><b>${label}:</b> <span style="color:var(--green);font-size:0.85em;">✅ Nessun ritardo significativo</span></div>`;
  const pills = lista.map(r => `<span class="tag tag-${r.peso >= 2.5 ? 'rosso' : (r.peso >= 1.5 ? 'giallo' : 'verde')}">${esc(r.label)}</span>`).join(' ');
  return `<div><b>${label}:</b> ${pills}</div>`;
}

function partitaHtml(camp, m) {
  const degr = m.n_degradati > 0 ? ' ⚠️' : '';
  const [bk, bp, bq, breal] = m.best_1x2;
  const titolo = bk !== 'No Segno Fisso'
    ? `🕒 ${esc(m.orario)} | 🏟️ ${esc(m.c_u)} vs ${esc(m.t_u)} | 👑 ${esc(bk)}${degr}`
    : `🕒 ${esc(m.orario)} | 🏟️ ${esc(m.c_u)} vs ${esc(m.t_u)} | ⚠️ No Bet${degr}`;
  let tags = '';
  if (m.msg_mot) tags += `<span class="tag tag-giallo">${esc(m.msg_mot)}</span> `;
  if (m.msg_pressione) tags += `<span class="tag tag-rosso">${esc(m.msg_pressione.trim())}</span> `;
  if (m.andata_msg) tags += `<span class="tag tag-blu">${esc(m.andata_msg)}</span> `;
  if (m.streak_msg) tags += `<span class="tag tag-rosso">${esc(m.streak_msg)}</span> `;

  let pick;
  if (bk === 'No Segno Fisso') {
    pick = `<div class="pick-card" style="border-color:#3d1515;"><div style="font-size:2rem;margin:8px 0;">⚠️</div>
      <div style="font-family:'Syne',sans-serif;font-weight:700;color:#f87171;">NESSUN SEGNO SICURO</div>
      <div style="font-size:0.8rem;color:var(--text2);margin-top:8px;">Usa Combo o Multigol</div></div>`;
  } else {
    const edgeV = calcolaEdgePct(bp, Number(bq)); const kellyV = kellyFraction(bp, Number(bq));
    pick = `<div class="pick-card"><div style="font-size:0.75rem;color:var(--text2);text-transform:uppercase;letter-spacing:0.1em;">👑 Miglior Segno</div>
      <div class="pick-sign">${esc(bk)}</div>
      <div class="pick-prob">Probabilità stimata: <strong style="color:var(--text)">${fmt(bp, 1)}%</strong></div>
      <div style="margin-bottom:10px;"><span class="${edgeV > 0 ? 'edge-positive' : 'edge-negative'}">Edge ${sgn(edgeV, 1)}%</span>
      <span class="kelly-pill">Kelly ${fmt(kellyV * 100, 1)}%</span></div>
      <div><span class="${breal ? 'quota-real' : 'quota-calc'}">${breal ? 'Bet365' : 'V90 Est.'}: ${esc(bq)}</span></div></div>`;
  }

  const excl = new Set(['U4.5', 'O0.5', 'O1.5', 'Casa O0.5', 'Ospite O0.5']);
  const top3 = [...m.all_tips].filter(([k]) => !excl.has(k)).sort((a, b) => b[1] - a[1]).slice(0, 3);
  const medaglie = ['🥇', '🥈', '🥉'];
  let righe = ''; const top3Det = [];
  top3.forEach(([tk, tv], i) => {
    const [qf, qreal] = getQuotaFinale(tk, tv, m.quote_reali);
    const ef = calcolaEdgePct(tv, qf);
    righe += `<div class="top3-row"><span>${medaglie[i]} <span class="top3-tip">${esc(tk)}</span><span class="top3-prob" style="margin-left:6px;">${fmt(tv, 0)}%</span></span>
      <span><span class="${ef > 0 ? 'edge-positive' : 'edge-negative'}">${sgn(ef, 0)}%</span> <span class="${qreal ? 'quota-real' : 'quota-calc'}" style="margin-left:4px;">Q${esc(qf)}</span></span></div>`;
    top3Det.push({ tip: tk, prob: tv, quota: qf, real: qreal, edge: ef, medal: medaglie[i] });
  });

  const matchStr = `${m.c_u} vs ${m.t_u}`;
  let candidati = [];
  if (bk !== 'No Segno Fisso') candidati.push({
    label: `👑 ${bk} (Q ${bq})`, Match: matchStr, Tip: bk, Prob: bp, Quota: bq, Real: breal,
    Edge: calcolaEdgePct(bp, Number(bq)), Kelly: kellyFraction(bp, Number(bq)),
  });
  for (const d of top3Det) candidati.push({
    label: `${d.medal} ${d.tip} (Q ${d.quota})`, Match: matchStr, Tip: d.tip, Prob: d.prob, Quota: d.quota, Real: d.real,
    Edge: d.edge, Kelly: kellyFraction(d.prob, Number(d.quota)),
  });
  const visti = new Set(); candidati = candidati.filter(c => !visti.has(c.Tip) && visti.add(c.Tip));
  const checks = candidati.map(c => {
    const item = { ...c, League: camp, Time: m.orario, FixtureID: m.fixture_id };
    S.righeTabella.set(chiaveSel(item), item);
    return `<label class="inline-ctl" style="margin:0;"><input type="checkbox" data-cart="${esc(chiaveSel(item))}" data-src="t2"${S.carrello.has(chiaveSel(item)) ? ' checked' : ''}> ${esc(c.label)}</label>`;
  }).join('');

  const corpo = `
    <div style="font-size:0.85em;color:#7f8c8d;margin-bottom:10px;"><b>Arbitro:</b> ${esc(m.arb)} | <b>VAR:</b> ${m.is_sev ? '⚠️ Fiscale' : '⚖️ Standard'} | <b>Clima:</b> ${esc(m.meteo)}</div>
    ${m.msg_radar ? `<div class="alert alert-warn">${esc(m.msg_radar)}</div>` : ''}
    ${tags ? `<div style="margin-bottom:15px;">${tags}</div>` : ''}
    <h3>🎯 PREVISIONI MATRIX V90</h3>
    <div class="cols cols-pick">${pick}<div class="top3-card"><div class="section-header" style="margin-bottom:12px;"><span style="font-family:Syne,sans-serif;font-weight:700;font-size:0.9rem;">🔝 TOP 3 OMNI-MARKET</span></div>${righe}</div></div>
    ${checks ? `<div style="margin-top:10px;"><b>➕ Aggiungi alle mie schedine:</b><div class="cols" style="grid-template-columns:repeat(${candidati.length},auto);justify-content:start;gap:20px;margin-top:6px;">${checks}</div></div>` : ''}
    <hr><h3>📊 CONFRONTO FORZE IN CAMPO</h3>
    <div class="cols cols-vs">
      ${schedaSquadra(m.c_s, m.rank_c, m.xg_c, m.forma_c, m.stan_c, m.count_c, m.t1_c, m.sq_c, m.gk_out_c, m.def_out_c, m.stile_c, m.poss_c, m.parate_c, m.conv_c, m.cs_c, m.fts_c, '🏠', camp)}
      <div class="vs-badge">VS</div>
      ${schedaSquadra(m.t_s, m.rank_t, m.xg_t, m.forma_t, m.stan_t, m.count_t, m.t1_t, m.sq_t, m.gk_out_t, m.def_out_t, m.stile_t, m.poss_t, m.parate_t, m.conv_t, m.cs_t, m.fts_t, '✈️', camp)}
    </div><hr>
    <div class="cols cols-pick">
      <div><b>Metriche Gara</b><div>🚩 Corner: <b>${fmt(m.corn_tot, 1)}</b> | 🟨 Cartellini: <b>${fmt(m.cart_tot, 1)}</b> | 🛑 Falli: <b>${fmt(m.falli_tot, 1)}</b></div></div>
      <div><b>Ritardi &amp; Storico</b>${renderRitardi(m.rit_c, 'Ritardi Casa')}${renderRitardi(m.rit_t, 'Ritardi Ospite')}
        <div><b>DNA:</b> <span class="dna-testo">${esc(m.dna_h2h)}</span></div>
        ${m.dettagli_h2h ? dettagli(`h2h_${m.fixture_id}`, '🔍 Ultimi 5 Scontri Diretti', `<div class="h2h-box">${htmlSicuro(m.dettagli_h2h)}</div>`) : ''}</div>
    </div>`;
  return dettagli(`m_${m.fixture_id}`, titolo, corpo);
}

function renderTab2() {
  let html = `<div>Partite per il periodo <b>${esc(S.start)} / ${esc(S.end)}</b>.</div>`;
  for (const [camp, matches] of S.dataMaster) {
    const aff = matches.map(m => m.aff_dinamica ?? getAffidabilita(camp))
      .reduce((p, a) => (AFFIDABILITA_ORDINE[a] ?? 2) < (AFFIDABILITA_ORDINE[p] ?? 2) ? a : p, getAffidabilita(camp));
    const nDegr = matches.filter(m => m.n_degradati > 0).length;
    const [icona, colore, desc] = AFFIDABILITA_BADGE[aff];
    const corpo = `<span class="tag" style="background:${colore}22;border:1px solid ${colore}55;color:${colore};">${icona} Affidabilità ${aff} — ${esc(desc)}</span>
      ${nDegr > 0 ? `<div class="muted small">⚠️ ${nDegr}/${matches.length} partite con almeno una fonte dati caduta in fallback in questa sessione (vedi ⚠️ nel titolo).</div>` : ''}
      ${[...matches].sort((a, b) => a.ts - b.ts).map(m => partitaHtml(camp, m)).join('')}`;
    html += dettagli(`camp_${camp}`, `🏆 ${esc(camp)}  ${icona}`, corpo);
  }
  return html;
}

// ═══════════════ TAB 3 — SCHEDINE AUTOMATICHE ═══════════════
const SCHEDINE_CFG = [
  { nome: 'SAFETY', emoji: '🟢', cls: 'safety-bg', bg: '#0a1f0f', acc: '#22c55e', nota: 'Solo scommesse con edge > 0%, quota 1.12–1.50.' },
  { nome: 'PERFORMANCE', emoji: '🟠', cls: 'performance-bg', bg: '#1f140a', acc: '#f59e0b', nota: 'Quote medie, max un evento per partita.' },
  { nome: 'AZZARDO', emoji: '🔴', cls: 'risk-bg', bg: '#1f0a0a', acc: '#ef4444', nota: 'Quote alte — max 10% del capitale.' },
];
const NOTE_PROB = [
  'Le gambe più probabili per il modello, quote reali bet365, max 3 gambe',
  'Le gambe più probabili, quote medie, max un evento per partita',
  'Le gambe più probabili tra le quote alte — max 10% del capitale',
];

function paramsMetodo(metodo, budgetTot) {
  const bud = [budgetTot * 0.60, budgetTot * 0.30, budgetTot * 0.10];
  const ordina = metodo === 'edge' ? 'edge' : 'prob';
  return [
    { minQ: 1.12, maxQ: 1.50, target: 2.0, mq: 2.0, hard: null, budget: bud[0], maxRighe: 3, ordina },
    { minQ: 1.51, maxQ: 2.20, target: 5.0, mq: 2.20, hard: null, budget: bud[1], maxRighe: 12, ordina },
    { minQ: 2.21, maxQ: 4.50, target: 30.0, mq: 4.50, hard: 50.0, budget: bud[2], maxRighe: 12, ordina },
  ];
}

export async function generaSchedine() {
  const kp = S.allTips;
  if (kp.length < 4) return { html: '<div class="alert">Troppe poche selezioni per comporre le schedine.</div>', testo: '' };
  const oggi = oggiStr();
  let testoExport = `=== MATRIX V90: SCHEDINE ===\nPeriodo: ${S.start}/${S.end}\n\n`;
  const salvataggi = [];
  const METODI = [
    { key: 'prob', prefisso: 'PROB_', titolo: '🎯 Metodo Probabilità — le schedine da giocare', exp: false },
    { key: 'edge', prefisso: '', titolo: '📎 Confronto: metodo Edge (solo tracking, senza soldi veri)', exp: true },
  ];
  let htmlTot = '';
  for (const met of METODI) {
    let escludiPrev = new Set();
    let htmlMetodo = '';
    const P = paramsMetodo(met.key, S.budgetTotale);
    SCHEDINE_CFG.forEach((cfg, idx) => {
      const p = P[idx];
      const nota = met.key === 'prob' ? `${NOTE_PROB[idx]} (quota per gamba ${fmt(p.minQ)}–${fmt(p.maxQ)}).` : cfg.nota;
      const escludi = escludiPrev;
      const [slip, qTot, prob, usate] = costruisciSchedinaDinamica(kp, p.minQ, p.maxQ, p.target, {
        escludiMatch: escludi, maxMatchQ: p.mq, maxRighe: p.maxRighe, ordinaPer: p.ordina,
        maxQuotaFinale: p.hard, soloEdgePositivo: met.key === 'edge', soloQuoteReali: met.key === 'prob',
      });
      escludiPrev = usate;
      const vincita = p.budget * qTot;
      const candidati = kp.filter(x => p.minQ <= Number(x.Quota) && Number(x.Quota) <= p.mq && Number(x.Quota) <= p.maxQ
        && (met.key !== 'edge' || Number(x.Edge ?? 0) > 0) && (met.key !== 'prob' || !!x.Real) && !escludi.has(x.Match));
      const nCand = candidati.length; const nMatchCand = new Set(candidati.map(x => x.Match)).size;
      if (slip.length) salvataggi.push(salvaSchedina(`${met.prefisso}${cfg.nome}`, oggi, slip, qTot, prob, p.budget, met.key));

      const testata = (extra = '') => `<div style="background:linear-gradient(135deg,${cfg.bg},${cfg.bg}dd);padding:18px 24px 14px;border-bottom:1px solid rgba(255,255,255,0.06);">
        <div style="display:flex;align-items:center;justify-content:space-between;"><div>
        <div style="font-family:'Syne',sans-serif;font-size:1.2rem;font-weight:800;color:${cfg.acc};">${cfg.emoji} Schedina ${cfg.nome}</div>
        <div style="font-size:0.75rem;color:var(--text2);margin-top:3px;">${esc(nota)}</div>${extra}</div>
        <div style="text-align:right;"><div style="font-size:0.72rem;color:var(--text2);text-transform:uppercase;letter-spacing:0.08em;">Budget</div>
        <div style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:700;color:var(--text);">${fmt(p.budget)}€</div></div></div></div>`;

      if (idx === 0 && !slip.length) {
        const motivo = `${nCand} selezioni idonee disponibili oggi (quota 1.12-1.50, ${met.key === 'edge' ? 'edge positivo' : 'quote reali'}) su ${nMatchCand} partite diverse — non bastano per comporre nemmeno una combinazione minima`;
        htmlMetodo += `<div class="strategy-box ${cfg.cls}" style="padding:0;overflow:hidden;">${testata()}
          <div style="padding:16px 24px;color:var(--text2);font-size:0.9rem;">Nessuna combinazione trovata oggi (${esc(motivo)}) — meglio saltare la Safety oggi piuttosto che proporre una combo incompleta.</div></div>`;
        testoExport += `Schedina ${cfg.nome}: saltata, ${motivo}.\n\n`;
        return;
      }

      let txt = `[${met.key}] Schedina ${cfg.nome} (${fmt(p.budget)}€)\n`;
      let righe = '';
      for (const x of slip) {
        const ed = x.Edge ?? 0; const kl = (x.Kelly ?? 0) * 100; const pt = S.budgetTotale * (x.Kelly ?? 0);
        const pill = met.key === 'prob'
          ? `<span class="edge-positive">P ${fmt(x.Prob, 0)}%</span>`
          : `<span class="${ed > 0 ? 'edge-positive' : 'edge-negative'}">${sgn(ed, 0)}%</span> <span class="kelly-pill">${fmt(kl, 1)}% → ${fmt(pt)}€</span>`;
        righe += `<div class="schedina-row"><div><div style="font-weight:600;color:var(--text);">
          <span style="color:var(--orange);font-family:DM Mono,monospace;font-size:0.8rem;">[${esc(x.Time)}]</span> ${esc(x.Match)} → <strong>${esc(x.Tip)}</strong></div>
          <div class="schedina-match">${esc(x.League)}</div></div>
          <div style="text-align:right;white-space:nowrap;"><span class="${x.Real ? 'quota-real' : 'quota-calc'}">Q ${esc(x.Quota)}</span> ${pill}</div></div>`;
        txt += met.key === 'prob'
          ? `  [${x.Time}] ${x.Match} -> ${x.Tip} @ ${fmt(x.Quota)} | Prob:${fmt(x.Prob, 1)}%\n`
          : `  [${x.Time}] ${x.Match} -> ${x.Tip} @ ${fmt(x.Quota)} | Edge:${sgn(ed, 1)}% | Kelly:${fmt(kl, 1)}% (${fmt(pt)}€)\n`;
      }
      htmlMetodo += `<div class="strategy-box ${cfg.cls}" style="padding:0;overflow:hidden;">
        ${testata(`<div style="font-size:0.7rem;color:var(--text2);margin-top:2px;opacity:0.7;">ℹ️ ${nCand} selezioni idonee oggi su ${nMatchCand} partite — usate ${slip.length}</div>`)}
        <div style="padding:16px 24px;">${righe}
        <div style="margin-top:14px;padding:14px 16px;background:rgba(255,255,255,0.04);border-radius:var(--radius-sm);border:1px solid rgba(255,255,255,0.07);display:flex;align-items:center;justify-content:space-between;">
          <div style="display:flex;align-items:center;gap:20px;">
            <div><div style="font-size:0.7rem;color:var(--text2);text-transform:uppercase;letter-spacing:0.08em;">Moltiplicatore</div>
            <div style="font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:800;color:${cfg.acc};">x${fmt(qTot)}</div></div>
            <div><div style="font-size:0.7rem;color:var(--text2);text-transform:uppercase;letter-spacing:0.08em;">Prob. congiunta</div>
            <div style="font-family:'DM Mono',monospace;font-size:1rem;font-weight:600;color:var(--text);">${fmt(prob * 100, 1)}%</div></div></div>
          <div style="text-align:right;"><div style="font-size:0.7rem;color:var(--text2);text-transform:uppercase;letter-spacing:0.08em;">Vincita stimata</div>
          <div style="font-family:'Syne',sans-serif;font-size:1.4rem;font-weight:800;color:var(--green);">~${fmt(vincita)}€</div></div></div></div></div>`;
      txt += `Quota:${fmt(qTot)} | Prob:${fmt(prob * 100)}% | Vincita:~${fmt(vincita)}€\n\n`;
      testoExport += txt;
    });
    htmlTot += met.exp ? dettagli(`metodo_${met.key}`, met.titolo, htmlMetodo) : `<h3>${met.titolo}</h3>${htmlMetodo}`;
  }
  const esiti = await Promise.all(salvataggi);
  const falliti = esiti.filter(ok => !ok).length;
  const stato = salvataggi.length
    ? (falliti ? `<div class="alert alert-err">❌ ${falliti} schedine non salvate su Firebase — controlla la console.</div>`
               : `<div class="muted small">✅ ${salvataggi.length} schedine salvate su Firebase per il tracking.</div>`)
    : '';
  return { html: `${stato}${htmlTot}<div class="inline-ctl"><button class="btn" data-az="scarica-schedine">💾 SCARICA TUTTE LE SCHEDINE (TXT)</button></div>`, testo: testoExport };
}

// ═══════════════ ASSEMBLAGGIO ═══════════════
export async function renderEstrazione() {
  const box = $('#box-estrazione');
  if (!S.dataMaster.size) { box.innerHTML = ''; return; }
  S.righeTabella = new Map();
  const t1 = renderTab1();
  const t2 = renderTab2();
  box.innerHTML = `<div class="tabs">
      <button class="tab" data-tab="t1">🛒 TOP 10 &amp; BUILDER</button>
      <button class="tab" data-tab="t2">🔬 ESPLORATORE PARTITE</button>
      <button class="tab" data-tab="t3">🏆 SCHEDINE AUTOMATICHE</button></div>
    <div id="tab-t1" class="tabpane">${t1}</div><div id="tab-t2" class="tabpane">${t2}</div>
    <div id="tab-t3" class="tabpane"><h2>🏆 Generatore Automatico Ottimizzato V90</h2>
      <div class="muted small">💡 Budget per fascia: ripartizione fissa 60/30/10. Metodo Probabilità = le gambe più sicure per il modello (quelle che si giocano); metodo Edge = solo confronto.</div>
      <div id="schedine-contenuto"><div class="alert">Calcolo e salvataggio delle schedine…</div></div></div>`;
  mostraTab(S.tabAttivo);
  renderCarrello();
  await aggiornaSchedine();
}

export async function aggiornaSchedine() {
  const c = $('#schedine-contenuto');
  if (!c) return;
  const { html, testo } = await generaSchedine();
  S.testoSchedine = testo;
  const c2 = $('#schedine-contenuto');
  if (c2) c2.innerHTML = html;
  ricaricaStorico();
}

function mostraTab(t) {
  S.tabAttivo = t;
  for (const b of $$('.tab')) b.classList.toggle('attivo', b.dataset.tab === t);
  for (const p of $$('.tabpane')) p.classList.toggle('hidden', p.id !== `tab-${t}`);
}

export function inizializzaEstrazione() {
  const box = $('#box-estrazione');
  box.addEventListener('click', async e => {
    const tab = e.target.closest('[data-tab]');
    if (tab) return mostraTab(tab.dataset.tab);
    const btn = e.target.closest('button[data-az]');
    if (!btn) return;
    if (btn.dataset.az === 'scarica-carrello') scaricaFile(`Matrix_${timestampFile()}.txt`, S.testoCarrello);
    else if (btn.dataset.az === 'scarica-schedine') scaricaFile(`Matrix_V90_${timestampFile()}.txt`, S.testoSchedine);
    else if (btn.dataset.az === 'salva-personale') {
      const stake = parseFloat($('#stake-personale').value) || 10;
      const d = new Date(); const p = n => String(n).padStart(2, '0');
      const nome = `PERSONALE_${p(d.getHours())}${p(d.getMinutes())}${p(d.getSeconds())}`;
      const { qTot, probTot } = S.carrelloTot;
      btn.disabled = true;
      const ok = await salvaGiocataPersonale(nome, oggiStr(), [...S.carrello.values()], qTot, probTot, stake);
      btn.disabled = false;
      if (ok) { avviso('✅ Salvata! La trovi nello Storico Schedine in cima alla pagina.', 'ok'); ricaricaStorico(); }
      else avviso('❌ Errore nel salvataggio — controlla la console.', 'err');
    }
  });
  box.addEventListener('change', e => {
    const cb = e.target.closest('input[data-cart]');
    if (!cb) return;
    const k = cb.dataset.cart;
    if (cb.checked) { const item = S.righeTabella.get(k); if (item) S.carrello.set(k, item); }
    else S.carrello.delete(k);
    sincronizzaCheckbox();
    renderCarrello();
  });
}
