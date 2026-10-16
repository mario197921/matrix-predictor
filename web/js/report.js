// report.js — Report analitico e simulazione bankroll virtuale (port di
// matrix_modello.py). Funzioni pure: ricevono lo storico già letto da Firestore.
import { getFamily, pyRound } from './modello.js';

export const FASCE_QUOTA = [
  [0.0, 1.30, '< 1.30'], [1.30, 1.50, '1.30 - 1.49'], [1.50, 2.00, '1.50 - 1.99'],
  [2.00, 3.00, '2.00 - 2.99'], [3.00, 5.00, '3.00 - 4.99'], [5.00, Infinity, '5.00+'],
];

export function fasciaQuota(q) {
  for (const [lo, hi, nome] of FASCE_QUOTA) if (lo <= q && q < hi) return nome;
  return FASCE_QUOTA[FASCE_QUOTA.length - 1][2];
}

const nuovaStat = () => ({ vinte: 0, perse: 0, attesa: 0, quotaSum: 0.0, quotaN: 0 });

function registraGamba(stat, esitoGamba, quota) {
  if (esitoGamba === 'vinta') stat.vinte++;
  else if (esitoGamba === 'persa') stat.perse++;
  else { stat.attesa++; return; }
  if (quota) { stat.quotaSum += Number(quota); stat.quotaN++; }
}

function finalizzaStat(s) {
  const concluse = s.vinte + s.perse;
  const winRate = concluse ? pyRound(s.vinte / concluse * 100, 1) : null;
  const quotaMedia = s.quotaN ? pyRound(s.quotaSum / s.quotaN, 3) : null;
  const probImp = quotaMedia ? pyRound(100.0 / quotaMedia, 1) : null;
  const edgeVs = (winRate !== null && probImp !== null) ? pyRound(winRate - probImp, 1) : null;
  return {
    vinte: s.vinte, perse: s.perse, attesa: s.attesa, concluse,
    'win_rate_%': winRate, quota_media_concluse: quotaMedia,
    'prob_implicita_media_%': probImp, 'edge_vs_implicita_%': edgeVs,
  };
}

export function eRealeRecord(r) {
  return r.fonte === 'bet365_manuale' || String(r.nome ?? '').startsWith('PERSONALE_') || !!r.giocata_reale;
}
export function eSoloPersonaleORealeManuale(r) {
  return r.fonte === 'bet365_manuale' || String(r.nome ?? '').startsWith('PERSONALE_');
}
export const esitoRealeEffettivoRecord = r => r.esito_reale || r.esito;
export const metodoRecord = r => r.metodo || 'edge';

export function tierRecord(r) {
  let nome = String(r.nome ?? '');
  if (nome.startsWith('PROB_')) nome = nome.slice(5);
  return ['SAFETY', 'PERFORMANCE', 'AZZARDO'].includes(nome) ? nome : 'ALTRO';
}

// Chiave per ordinare dalla PIÙ VECCHIA alla più recente (come in Python).
export function chiaveCronologica(r) {
  const d = String(r.data ?? '');
  const nome = String(r.nome ?? '');
  if (d.length === 10 && d[4] === '-' && d[7] === '-' && /^\d{4}$/.test(d.slice(0, 4))) return [1, d, nome];
  if (d.startsWith('storico_') && /^\d+$/.test(d.slice(8))) return [0, String(parseInt(d.slice(8), 10)).padStart(6, '0'), nome];
  return [0, d, nome];
}
export function confrontaChiavi(a, b) {
  for (let i = 0; i < a.length; i++) {
    if (a[i] < b[i]) return -1;
    if (a[i] > b[i]) return 1;
  }
  return 0;
}

export function simulaBankrollVirtuale(storico, puntata = 1.0, bankrollIniziale = 10.0) {
  const ordinate = [...storico].sort((x, y) => confrontaChiavi(chiaveCronologica(x), chiaveCronologica(y)));
  const curva = []; const perGruppo = {};
  let nAttesa = 0; let nSenzaQuota = 0; let plCum = 0.0; let picco = 0.0; let maxDd = 0.0;
  let bank = Number(bankrollIniziale); let fermatoAlla = null; let giocateBank = 0; let nConcluse = 0;

  for (const r of ordinate) {
    const esito = r.esito;
    if (esito !== 'vinta' && esito !== 'persa') { nAttesa++; continue; }
    const q0 = r.quota_totale;
    if (!q0 || Number(q0) <= 1.0) { nSenzaQuota++; continue; }
    const q = Number(q0);
    nConcluse++;
    const pl = esito === 'vinta' ? puntata * (q - 1.0) : -puntata;
    plCum += pl; picco = Math.max(picco, plCum); maxDd = Math.max(maxDd, picco - plCum);

    const tier = tierRecord(r);
    const gruppo = tier !== 'ALTRO' ? `${metodoRecord(r)}/${tier}` : 'manuali_personali';
    const g = perGruppo[gruppo] ??= { concluse: 0, vinte: 0, puntato: 0.0, pl: 0.0 };
    g.concluse++; g.vinte += esito === 'vinta' ? 1 : 0; g.puntato += puntata; g.pl += pl;

    if (fermatoAlla === null) {
      if (bank + 1e-9 >= puntata) { bank += pl; giocateBank++; } else fermatoAlla = nConcluse;
    }
    curva.push({
      n: nConcluse, data: r.data, nome: r.nome, metodo: metodoRecord(r), quota: pyRound(q, 2),
      esito, pl: pyRound(pl, 2), pl_cumulato: pyRound(plCum, 2), bankroll_limitato: pyRound(bank, 2),
    });
  }
  const nVinte = curva.filter(x => x.esito === 'vinta').length;
  const puntatoTot = puntata * nConcluse;
  const per_gruppo = {};
  for (const [k, v] of Object.entries(perGruppo)) {
    per_gruppo[k] = {
      concluse: v.concluse, vinte: v.vinte, 'win_rate_%': pyRound(v.vinte / v.concluse * 100, 1),
      puntato: pyRound(v.puntato, 2), pl: pyRound(v.pl, 2), 'roi_%': pyRound(v.pl / v.puntato * 100, 1),
    };
  }
  return {
    puntata, bankroll_iniziale: bankrollIniziale, n_schedine_concluse: nConcluse,
    n_vinte: nVinte, n_perse: nConcluse - nVinte, n_in_attesa_escluse: nAttesa,
    n_senza_quota_escluse: nSenzaQuota, puntato_totale: pyRound(puntatoTot, 2),
    pl_totale: pyRound(plCum, 2), 'roi_%': puntatoTot ? pyRound(plCum / puntatoTot * 100, 1) : null,
    max_drawdown: pyRound(maxDd, 2),
    bankroll_limitato: { saldo_finale: pyRound(bank, 2), giocate_effettive: giocateBank, fermato_alla_schedina_n: fermatoAlla },
    per_gruppo, curva,
  };
}

const wr = (v, p) => ((v + p) ? pyRound(v / (v + p) * 100, 1) : null);

export function costruisciReportAnalitico(storico, budgetIniziale = 0.0) {
  const fascia = {}; const famiglia = {}; const lega = {}; const nGambeSt = {};
  const tierSt = {}; const metodoSt = {}; const giornoSt = {};
  let puntatoRealeTot = 0.0; let saldoRealeTot = 0.0; let nOverride = 0; let nReali = 0;

  for (const r of storico) {
    const selezioni = r.selezioni ?? [];
    for (const s of selezioni) {
      const q = s.quota; const eg = s.esito_gamba;
      if (q !== undefined && q !== null) registraGamba(fascia[fasciaQuota(Number(q))] ??= nuovaStat(), eg, q);
      const tipS = s.tip || s.Tip || '';
      if (tipS) registraGamba(famiglia[getFamily(tipS)] ??= nuovaStat(), eg, q);
      registraGamba(lega[s.league || '?'] ??= nuovaStat(), eg, q);
    }
    const nGambe = selezioni.length;
    const chiaveN = nGambe < 6 ? String(nGambe) : '6+';
    const esitoCalc = r.esito;
    const bump = o => { if (esitoCalc === 'vinta') o.vinte++; else if (esitoCalc === 'persa') o.perse++; else o.attesa++; };
    bump(nGambeSt[chiaveN] ??= { vinte: 0, perse: 0, attesa: 0 });
    const tier = tierRecord(r);
    bump(metodoSt[tier !== 'ALTRO' ? metodoRecord(r) : 'manuali_personali'] ??= { vinte: 0, perse: 0, attesa: 0 });
    const statT = tierSt[tier] ??= { vinte: 0, perse: 0, attesa: 0, puntato: 0.0, saldo: 0.0 };
    bump(statT);
    if (r.esito_reale) nOverride++;
    const g = giornoSt[r.data ?? '?'] ??= { vinte: 0, perse: 0, attesa: 0, saldo: 0.0 };
    bump(g);

    if (eRealeRecord(r)) {
      nReali++;
      if (r.puntata_reale !== undefined && r.puntata_reale !== null) {
        const p = Number(r.puntata_reale);
        statT.puntato += p; puntatoRealeTot += p;
        const eff = esitoRealeEffettivoRecord(r);
        let saldoRiga = 0.0;
        if (eff === 'vinta') {
          const v = r.vincita_reale;
          saldoRiga = (v !== undefined && v !== null) ? Number(v) - p : p * (r.quota_totale || 0) - p;
        } else if (eff === 'persa') saldoRiga = -p;
        statT.saldo += saldoRiga; saldoRealeTot += saldoRiga; g.saldo += saldoRiga;
      }
    }
  }

  const mapObj = (o, f) => Object.fromEntries(Object.entries(o).map(([k, v]) => [k, f(v)]));
  const conc = v => ({ ...v, concluse: v.vinte + v.perse, 'win_rate_%': wr(v.vinte, v.perse) });
  return {
    per_fascia_quota: mapObj(fascia, finalizzaStat),
    per_famiglia_mercato: mapObj(famiglia, finalizzaStat),
    per_lega: Object.fromEntries(Object.entries(lega).filter(([, v]) => v.vinte + v.perse >= 3).map(([k, v]) => [k, finalizzaStat(v)])),
    per_numero_gambe: mapObj(nGambeSt, conc),
    per_tier: mapObj(tierSt, v => ({
      vinte: v.vinte, perse: v.perse, attesa: v.attesa, concluse: v.vinte + v.perse,
      'win_rate_%': wr(v.vinte, v.perse), puntato_reale: pyRound(v.puntato, 2), saldo_reale: pyRound(v.saldo, 2),
    })),
    per_metodo: mapObj(metodoSt, conc),
    simulazione_virtuale: simulaBankrollVirtuale(storico, 1.0, budgetIniziale > 0 ? budgetIniziale : 10.0),
    andamento_giornaliero: Object.keys(giornoSt).sort().map(d => ({ data: d, ...giornoSt[d], saldo: pyRound(giornoSt[d].saldo, 2) })),
    riepilogo_reale: {
      n_schedine_reali: nReali, budget_iniziale: pyRound(budgetIniziale, 2),
      puntato_reale_tot: pyRound(puntatoRealeTot, 2), saldo_reale_tot: pyRound(saldoRealeTot, 2),
      saldo_attuale: pyRound(budgetIniziale + saldoRealeTot, 2),
      'roi_%': puntatoRealeTot ? pyRound(saldoRealeTot / puntatoRealeTot * 100, 1) : null,
      n_override_esito_reale: nOverride,
    },
    n_schedine_totali: storico.length,
  };
}
