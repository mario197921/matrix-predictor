// modello.js — Motore di calcolo puro (port di matrix_modello.py): Poisson/xG,
// quote, edge, Kelly, generazione schedine, valutazione esiti. Nessun I/O.
import { MARGINE_BK } from './leghe.js';

// round() di Python: corretto sul valore binario esatto, "al pari" sui veri
// pareggi (0.125 -> 0.12, 2.675 -> 2.67).
export function pyRound(x, n = 0) {
  if (!Number.isFinite(x)) return x;
  const esatto = Math.abs(x).toFixed(Math.min(100, n + 40));
  const [intero, dec = ''] = esatto.split('.');
  const resto = dec.slice(n);
  const tie = resto.length > 0 && resto[0] === '5' && /^0*$/.test(resto.slice(1));
  let r = Number(Math.abs(x).toFixed(n));
  if (tie) {
    // toFixed arrotonda i pareggi per eccesso: scegliamo il pari.
    const giu = Number((intero + '.' + dec.slice(0, n)).replace(/\.$/, ''));
    const cifra = n === 0 ? Number(intero.slice(-1)) : Number(dec[n - 1]);
    r = (cifra % 2 === 0) ? giu : r;
  }
  return x < 0 ? -r : r;
}

const FATTORIALE = [1, 1, 2, 6, 24, 120, 720, 5040];
export function calcolaProbPoisson(xg, gol) {
  return (Math.pow(xg, gol) * Math.exp(-xg)) / FATTORIALE[gol];
}

export function calcolaTuttiIMercati(xgC, xgT, avgCorner, avgCart, isSev, totFalli) {
  const kP = ['1', 'X', '2', '1X', 'X2', '12', 'Goal', 'NoGoal', 'Pari', 'Dispari', 'Casa O0.5', 'Ospite O0.5'];
  const LINEE = [1.5, 2.5, 3.5, 4.5];
  const p = {};
  for (const k of kP) p[k] = 0;
  for (const line of LINEE) { p[`U${line}`] = 0; p[`O${line}`] = 0; kP.push(`U${line}`, `O${line}`); }
  const kMG = ['MG 1-3', 'MG 1-4', 'MG 2-3', 'MG 2-4', 'MG 2-5', 'MG 3-4'];
  const mg = {};
  for (const k of kMG) mg[k] = 0;
  const re = {}; const kRE = [];

  for (let gc = 0; gc < 8; gc++) {
    for (let gt = 0; gt < 8; gt++) {
      const prob = calcolaProbPoisson(xgC, gc) * calcolaProbPoisson(xgT, gt) * 100.0;
      const tot = gc + gt;
      if (gc > gt) p['1'] += prob; else if (gc === gt) p['X'] += prob; else p['2'] += prob;
      if (gc > 0 && gt > 0) p['Goal'] += prob; else p['NoGoal'] += prob;
      if (tot % 2 === 0) p['Pari'] += prob; else p['Dispari'] += prob;
      for (const line of LINEE) {
        if (tot < line) p[`U${line}`] += prob; else p[`O${line}`] += prob;
      }
      if (gc > 0) p['Casa O0.5'] += prob;
      if (gt > 0) p['Ospite O0.5'] += prob;
      if (tot >= 1 && tot <= 3) mg['MG 1-3'] += prob;
      if (tot >= 1 && tot <= 4) mg['MG 1-4'] += prob;
      if (tot >= 2 && tot <= 3) mg['MG 2-3'] += prob;
      if (tot >= 2 && tot <= 4) mg['MG 2-4'] += prob;
      if (tot >= 2 && tot <= 5) mg['MG 2-5'] += prob;
      if (tot >= 3 && tot <= 4) mg['MG 3-4'] += prob;
      if (gc <= 4 && gt <= 4) { const k = `Risultato ${gc}-${gt}`; re[k] = prob; kRE.push(k); }
    }
  }
  p['1X'] = p['1'] + p['X'];
  p['X2'] = p['X'] + p['2'];
  p['12'] = p['1'] + p['2'];

  const combos = {
    '1X + Over 1.5':   (p['1X'] / 100) * (p['O1.5'] / 100) * 100 * 0.92,
    'X2 + Over 1.5':   (p['X2'] / 100) * (p['O1.5'] / 100) * 100 * 0.92,
    '1X + Under 3.5':  (p['1X'] / 100) * (p['U3.5'] / 100) * 100 * 0.95,
    'X2 + Under 3.5':  (p['X2'] / 100) * (p['U3.5'] / 100) * 100 * 0.95,
    '1 + Over 2.5':    (p['1'] / 100) * (p['O2.5'] / 100) * 100 * 0.90,
    '2 + Over 2.5':    (p['2'] / 100) * (p['O2.5'] / 100) * 100 * 0.90,
    'Goal + Over 2.5': (p['Goal'] / 100) * (p['O2.5'] / 100) * 100 * 0.95,
  };

  const htRaw = { '1': p['1'] * 0.9, 'X': p['X'] * 1.5, '2': p['2'] * 0.9 };
  const totHt = htRaw['1'] + htRaw['X'] + htRaw['2'];
  const htProb = { '1': htRaw['1'] / totHt, 'X': htRaw['X'] / totHt, '2': htRaw['2'] / totHt };
  const htft = {};
  for (const ht of ['1', 'X', '2']) for (const ft of ['1', 'X', '2']) {
    htft[`HT/FT ${ht}/${ft}`] = htProb[ht] * (p[ft] / 100.0) * 100.0;
  }

  const probCorner = Math.min(92.0, Math.max(15.0, (avgCorner / 9.5) * 55));
  const tension = avgCart + (isSev ? 1.5 : 0) + (totFalli / 20.0);
  const probCart = Math.min(88.0, Math.max(20.0, (tension / 5.0) * 55));
  const special = { 'Over 8.5 Angoli': probCorner, 'Over 4.5 Cartellini': probCart };

  // Map: preserva l'ordine d'inserimento di Python (le chiavi "1","2" in un
  // oggetto JS verrebbero riordinate).
  const out = new Map();
  for (const k of kP) out.set(k, p[k]);
  for (const k of kMG) out.set(k, mg[k]);
  for (const k of kRE) out.set(k, re[k]);
  for (const k of Object.keys(combos)) out.set(k, combos[k]);
  for (const k of Object.keys(htft)) out.set(k, htft[k]);
  for (const k of Object.keys(special)) out.set(k, special[k]);
  return out;
}

export function getQuotaFinale(tip, prob, quoteReali) {
  if (quoteReali && Object.prototype.hasOwnProperty.call(quoteReali, tip)) return [quoteReali[tip], true];
  if (prob <= 0) return [99.0, false];
  return [Math.max(1.01, pyRound((100.0 / prob) * MARGINE_BK, 2)), false];
}

export function calcolaEdgePct(prob, quota) { return ((prob / 100.0) * quota - 1.0) * 100.0; }

export function devig1x2(quoteReali) {
  if (!quoteReali || !['1', 'X', '2'].every(k => k in quoteReali)) return null;
  const grezze = {};
  for (const k of ['1', 'X', '2']) { const q = Number(quoteReali[k]); if (q > 0) grezze[k] = 1.0 / q; }
  if (Object.keys(grezze).length !== 3) return null;
  const tot = grezze['1'] + grezze['X'] + grezze['2'];
  if (tot <= 0) return null;
  return { '1': (grezze['1'] / tot) * 100.0, 'X': (grezze['X'] / tot) * 100.0, '2': (grezze['2'] / tot) * 100.0 };
}

export function blendProbMercato(probModello, probMercato, pesoMercato) {
  pesoMercato = Math.max(0.0, Math.min(1.0, pesoMercato));
  return probModello * (1.0 - pesoMercato) + probMercato * pesoMercato;
}

export function applicaBlendMercato1x2(fullTips, quoteReali, pesoMercato) {
  const pm = devig1x2(quoteReali);
  if (pm === null) return fullTips;
  const p = new Map(fullTips);
  for (const k of ['1', 'X', '2']) p.set(k, blendProbMercato(p.get(k), pm[k], pesoMercato));
  p.set('1X', p.get('1') + p.get('X'));
  p.set('X2', p.get('X') + p.get('2'));
  p.set('12', p.get('1') + p.get('2'));
  if (p.has('O1.5')) {
    p.set('1X + Over 1.5', (p.get('1X') / 100) * (p.get('O1.5') / 100) * 100 * 0.92);
    p.set('X2 + Over 1.5', (p.get('X2') / 100) * (p.get('O1.5') / 100) * 100 * 0.92);
  }
  if (p.has('U3.5')) {
    p.set('1X + Under 3.5', (p.get('1X') / 100) * (p.get('U3.5') / 100) * 100 * 0.95);
    p.set('X2 + Under 3.5', (p.get('X2') / 100) * (p.get('U3.5') / 100) * 100 * 0.95);
  }
  if (p.has('O2.5')) {
    p.set('1 + Over 2.5', (p.get('1') / 100) * (p.get('O2.5') / 100) * 100 * 0.90);
    p.set('2 + Over 2.5', (p.get('2') / 100) * (p.get('O2.5') / 100) * 100 * 0.90);
  }
  const htRaw = { '1': p.get('1') * 0.9, 'X': p.get('X') * 1.5, '2': p.get('2') * 0.9 };
  const totHt = htRaw['1'] + htRaw['X'] + htRaw['2'];
  if (totHt > 0) {
    for (const ht of ['1', 'X', '2']) for (const ft of ['1', 'X', '2']) {
      p.set(`HT/FT ${ht}/${ft}`, (htRaw[ht] / totHt) * (p.get(ft) / 100.0) * 100.0);
    }
  }
  return p;
}

export function kellyFraction(prob, quota, fraz = 0.08) {
  const p = prob / 100.0; const b = quota - 1.0;
  if (b <= 0) return 0.0;
  return Math.max(0.0, ((b * p - (1 - p)) / b) * fraz);
}

export function semplificaNome(nome) {
  for (const t of [' FC', ' AC', ' BC', ' AS', ' Calcio', ' AFC', ' SL']) nome = nome.split(t).join('');
  for (const t of ['FC ', 'AC ', 'AS ', 'AFC ', 'SL ']) if (nome.startsWith(t)) nome = nome.slice(t.length);
  return nome.trim();
}

export function blendPriorStagione(valoreCorrente, valorePrecedente, giocate, sogliaPartite = 10) {
  if (valorePrecedente === null || valorePrecedente === undefined) return valoreCorrente;
  const pesoPrec = Math.max(0.0, 1.0 - (giocate / sogliaPartite));
  return valoreCorrente * (1.0 - pesoPrec) + valorePrecedente * pesoPrec;
}

export function getFamily(tip) {
  if (['1', 'X', '2', '1X', 'X2', '12'].includes(tip)) return '1X2';
  if ((tip.includes('U') || tip.includes('O')) && !tip.includes('+')
      && !tip.includes('Casa') && !tip.includes('Ospite')
      && !tip.includes('Angoli') && !tip.includes('Cartellini')) return 'UO';
  if (tip.includes('MG')) return 'MG';
  if (tip.includes('Goal') || tip.includes('NoGoal')) return 'GGNG';
  if (tip.includes('+')) return 'COMBO';
  if (tip.includes('Risultato')) return 'RE';
  if (tip.includes('HT/FT')) return 'HTFT';
  if (['Pari', 'Dispari'].includes(tip)) return 'PD';
  if (tip.includes('Angoli') || tip.includes('Cartellini')) return 'SPECIAL';
  return 'ALTRO';
}

function* combinazioni(arr, k) {
  const n = arr.length;
  if (k > n) return;
  const idx = Array.from({ length: k }, (_, i) => i);
  while (true) {
    yield idx.map(i => arr[i]);
    let i = k - 1;
    while (i >= 0 && idx[i] === i + n - k) i--;
    if (i < 0) return;
    idx[i]++;
    for (let j = i + 1; j < k; j++) idx[j] = idx[j - 1] + 1;
  }
}

// Ritorna [sel, qTot, probTot, usati(Set)]
export function costruisciSchedinaDinamica(pool, minQ, maxQ, targetMult, opts = {}) {
  const {
    escludiMatch = new Set(), maxMatchQ = 5.0, maxRighe = 12, maxSameFamily = 2,
    maxInstabili = 1, ordinaPer = 'edge', minProbCongiunta = null, maxProbCongiunta = null,
    maxQuotaFinale = null, soloEdgePositivo = true, soloQuoteReali = false,
  } = opts;
  const escludi = new Set(escludiMatch);

  if (ordinaPer === 'prob_range') {
    const lo = minProbCongiunta === null ? 0.0 : minProbCongiunta;
    const hi = maxProbCongiunta === null ? 1.0 : maxProbCongiunta;
    const validPr = pool.filter(x => minQ <= Number(x.Quota) && Number(x.Quota) <= maxQ
      && Number(x.Quota) <= maxMatchQ && Number(x.Edge ?? 0) > 0 && !escludi.has(x.Match));
    const candidati = [...validPr]
      .sort((a, b) => calcolaEdgePct(b.Prob, Number(b.Quota)) - calcolaEdgePct(a.Prob, Number(a.Quota)))
      .slice(0, 30);
    if (candidati.length < maxRighe) return [[], 1.0, 1.0, new Set(escludi)];
    let miglior = null; let migliorEdge = null;
    for (const combo of combinazioni(candidati, maxRighe)) {
      const nomi = combo.map(c => c.Match);
      if (new Set(nomi).size !== nomi.length) continue;
      const fam = {}; let supera = false;
      for (const c of combo) {
        const f = getFamily(c.Tip); fam[f] = (fam[f] || 0) + 1;
        if (fam[f] > maxSameFamily) { supera = true; break; }
      }
      if (supera) continue;
      if (combo.filter(c => c.Instabile).length > maxInstabili) continue;
      let probJ = 1.0; let edgeTot = 0.0;
      for (const c of combo) { probJ *= c.Prob / 100.0; edgeTot += calcolaEdgePct(c.Prob, Number(c.Quota)); }
      if (lo <= probJ && probJ <= hi && (migliorEdge === null || edgeTot > migliorEdge)) { migliorEdge = edgeTot; miglior = combo; }
    }
    if (miglior === null) return [[], 1.0, 1.0, new Set(escludi)];
    let qTot = 1.0; let probTot = 1.0;
    for (const c of miglior) { qTot *= Number(c.Quota); probTot *= c.Prob / 100.0; }
    const usati = new Set(miglior.map(c => c.Match));
    return [miglior, qTot, probTot, new Set([...usati, ...escludi])];
  }

  const valid = pool.filter(x => minQ <= Number(x.Quota) && Number(x.Quota) <= maxQ
    && Number(x.Quota) <= maxMatchQ
    && (!soloEdgePositivo || Number(x.Edge ?? 0) > 0)
    && (!soloQuoteReali || !!x.Real));
  const poolOrd = ordinaPer === 'prob'
    ? [...valid].sort((a, b) => Number(b.Prob) - Number(a.Prob))
    : [...valid].sort((a, b) => calcolaEdgePct(b.Prob, Number(b.Quota)) - calcolaEdgePct(a.Prob, Number(a.Quota)));
  const sel = []; const viste = new Set(); const famCnt = {};
  let qTot = 1.0; let probTot = 1.0; let instabiliCnt = 0;
  for (const item of poolOrd) {
    const fam = getFamily(item.Tip); const nome = item.Match; const instabile = !!item.Instabile;
    if (!viste.has(nome) && !escludi.has(nome)
        && (famCnt[fam] || 0) < maxSameFamily
        && (!instabile || instabiliCnt < maxInstabili)) {
      if (maxQuotaFinale !== null && sel.length > 0 && qTot * Number(item.Quota) > maxQuotaFinale) continue;
      sel.push(item); viste.add(nome);
      famCnt[fam] = (famCnt[fam] || 0) + 1;
      if (instabile) instabiliCnt++;
      qTot *= Number(item.Quota); probTot *= item.Prob / 100.0;
    }
    if (qTot >= targetMult || sel.length >= maxRighe) break;
  }
  return [sel, qTot, probTot, new Set([...viste, ...escludi])];
}

export function costruisciRecordSchedina(nome, dataStr, selezioni, qTot, probTot, budget, creatoIl = null, metodo = 'edge') {
  if (creatoIl === null) creatoIl = new Date().toISOString();
  return {
    nome, data: dataStr, creato_il: creatoIl,
    quota_totale: pyRound(Number(qTot), 4),
    probabilita_congiunta: pyRound(Number(probTot), 4),
    budget: pyRound(Number(budget), 2),
    metodo,
    selezioni: selezioni.map(s => ({
      match: s.Match, tip: s.Tip,
      prob_dichiarata: pyRound(Number(s.Prob), 2),
      quota: pyRound(Number(s.Quota), 2),
      edge: pyRound(Number(s.Edge ?? 0), 2),
      league: s.League ?? '',
      fixture_id: s.FixtureID ?? null,
    })),
    esito: 'in_attesa',
  };
}

// ── Valutazione esiti reali ─────────────────────────────────────────────────
function segno1x2(c, t) { return c > t ? '1' : (c === t ? 'X' : '2'); }
function mappaParteCombo(parte) {
  if (parte.startsWith('Over ')) return 'O' + parte.slice(5);
  if (parte.startsWith('Under ')) return 'U' + parte.slice(6);
  return parte;
}

// true/false, oppure null se non valutabile automaticamente.
export function valutaEsitoTip(tip, gcFt, gtFt, gcHt = null, gtHt = null) {
  const totFt = gcFt + gtFt;
  if (tip === '1') return gcFt > gtFt;
  if (tip === 'X') return gcFt === gtFt;
  if (tip === '2') return gcFt < gtFt;
  if (tip === '1X') return gcFt >= gtFt;
  if (tip === 'X2') return gcFt <= gtFt;
  if (tip === '12') return gcFt !== gtFt;
  if (tip === 'Goal') return gcFt > 0 && gtFt > 0;
  if (tip === 'NoGoal') return !(gcFt > 0 && gtFt > 0);
  if (tip === 'Pari') return totFt % 2 === 0;
  if (tip === 'Dispari') return totFt % 2 !== 0;
  if (tip === 'Casa O0.5') return gcFt > 0;
  if (tip === 'Ospite O0.5') return gtFt > 0;
  if (tip.length > 1 && (tip[0] === 'O' || tip[0] === 'U') && /^(\d+\.?\d*|\.\d+)$/.test(tip.slice(1))) {
    const linea = parseFloat(tip.slice(1));
    return tip[0] === 'O' ? totFt > linea : totFt < linea;
  }
  if (tip.startsWith('MG ')) {
    const [lo, hi] = tip.slice(3).split('-');
    return parseInt(lo, 10) <= totFt && totFt <= parseInt(hi, 10);
  }
  if (tip.startsWith('Risultato ')) {
    const [gc, gt] = tip.slice(10).split('-');
    return gcFt === parseInt(gc, 10) && gtFt === parseInt(gt, 10);
  }
  if (tip.startsWith('HT/FT ')) {
    if (gcHt === null || gcHt === undefined || gtHt === null || gtHt === undefined) return null;
    const [ht, ft] = tip.slice(6).split('/');
    return segno1x2(gcHt, gtHt) === ht && segno1x2(gcFt, gtFt) === ft;
  }
  if (tip.includes(' + ')) {
    const parti = tip.split(' + ').map(mappaParteCombo);
    const esiti = parti.map(p => valutaEsitoTip(p, gcFt, gtFt, gcHt, gtHt));
    if (esiti.some(e => e === null)) return null;
    return esiti.every(e => e);
  }
  return null;
}
