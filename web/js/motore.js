// motore.js — Motore principale di estrazione (port del blocco "MOTORE
// PRINCIPALE" di app.py): scarica i dati, calcola xG e probabilità per ogni
// partita e produce l'elenco di tutte le selezioni (all_tips_global).
import {
  XG_MAX, XG_MIN, MASTER_LEAGUES, AFFIDABILITA_ORDINE, getAffidabilita,
  LEGHE_ANNO_SOLARE, LEGHE_PLAYOFF, COPPE_EUROPEE, LEGHE_CIECHE, COPPE_NAZIONALI,
} from './leghe.js';
import {
  apiGet, trovaIdMultipli, risolviIdPerNome, trovaIdCoppa, analizzaInfortuniPesatiV90,
  scaricaQuoteNative, analizzaStatisticheStagionali, analizzaStatisticheAvanzatePro,
  analizzaSquadraGlobale, analizzaH2hDnaEAndata, trovaLegaSquadra, rilevaContestoSpareggio,
  scaricaMeteo, scaricaStandingsPregressi, ErroreAutenticazione,
} from './api.js';
import {
  calcolaTuttiIMercati, getQuotaFinale, calcolaEdgePct, kellyFraction, semplificaNome,
  applicaBlendMercato1x2, blendPriorStagione,
} from './modello.js';

export function stagioneCorrente(oggi = new Date()) {
  return String(oggi.getMonth() + 1 >= 8 ? oggi.getFullYear() : oggi.getFullYear() - 1);
}

// ── Auto-discovery ID (Norvegia, sudamericane/MLS, coppe nazionali) ─────────
const CHIAVE_LS = 'matrix_leghe_v1';

export async function inizializzaLeghe() {
  try {
    const salvato = JSON.parse(localStorage.getItem(CHIAVE_LS) || 'null');
    if (salvato && Date.now() - salvato.ts < 86400000 && salvato.map) {
      for (const k of Object.keys(MASTER_LEAGUES)) delete MASTER_LEAGUES[k];
      Object.assign(MASTER_LEAGUES, salvato.map);
      for (const n of ['🇫🇮 Finnish Cup', '🇳🇴 Norwegian Cup', '🇸🇪 Svenska Cupen', '🇩🇰 DBU Pokalen']) LEGHE_ANNO_SOLARE.add(n);
      return;
    }
  } catch (e) { /* ricalcola */ }

  const noLeghe = await trovaIdMultipli('Norway', { Eliteserien: 69, 'Norwegian First Division': 70 });
  MASTER_LEAGUES['🇳🇴 Eliteserien'] = noLeghe['Eliteserien'] ?? 69;
  MASTER_LEAGUES['🇳🇴 1. divisjon (Playoff NO)'] = noLeghe['Norwegian First Division'] ?? 70;

  const risolvi = [
    ['🇵🇪 Liga 1 Perù', () => risolviIdPerNome('Peru', 'Liga 1', null)],
    ['🇵🇾 División Profesional PY', () => risolviIdPerNome('Paraguay', 'Division Profesional', null)],
    ['🇺🇸 MLS', () => risolviIdPerNome('USA', 'Major League Soccer', null)],
  ];
  const coppe = [
    ['🇫🇮 Finnish Cup', 'Finland', 'Finnish Cup', 391], ['🇳🇴 Norwegian Cup', 'Norway', 'Norwegian Football Cup', 112],
    ['🇸🇪 Svenska Cupen', 'Sweden', 'Svenska Cupen', 144], ['🇩🇰 DBU Pokalen', 'Denmark', 'DBU Pokalen', 123],
    ['🇮🇹 Coppa Italia', 'Italy', 'Coppa Italia', 137], ['🏴󠁧󠁢󠁥󠁮󠁧󠁿 FA Cup', 'England', 'FA Cup', 45],
    ['🏴󠁧󠁢󠁥󠁮󠁧󠁿 EFL Cup', 'England', 'League Cup', 48], ['🇪🇸 Copa del Rey', 'Spain', 'Copa del Rey', 143],
    ['🇩🇪 DFB Pokal', 'Germany', 'DFB Pokal', 81], ['🇫🇷 Coupe de France', 'France', 'Coupe de France', 66],
    ['🇳🇱 KNVB Beker', 'Netherlands', 'KNVB Beker', 90], ['🇵🇹 Taça de Portugal', 'Portugal', 'Taça de Portugal', 96],
    ['🇧🇪 Croky Cup', 'Belgium', 'Belgian Cup', 146], ['🇹🇷 Türkiye Kupası', 'Turkey', 'Türkiye Kupası', 204],
    ['🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Cup', 'Scotland', 'Scottish Cup', 283], ['🇨🇭 Schweizer Cup', 'Switzerland', 'Schweizer Cup', 208],
    ['🇦🇹 ÖFB Cup', 'Austria', 'ÖFB Cup', 219],
  ];
  const [rs, rc] = await Promise.all([
    Promise.all(risolvi.map(([, f]) => f())),
    Promise.all(coppe.map(([, naz, nome, fb]) => trovaIdCoppa(naz, nome, fb))),
  ]);
  risolvi.forEach(([n], i) => { MASTER_LEAGUES[n] = rs[i]; });
  coppe.forEach(([n], i) => { MASTER_LEAGUES[n] = rc[i]; });

  // Pulizia: leghe non risolte o con ID in collisione vengono escluse tutte.
  const conteggio = {};
  for (const v of Object.values(MASTER_LEAGUES)) conteggio[v] = (conteggio[v] || 0) + 1;
  for (const k of Object.keys(MASTER_LEAGUES)) {
    const v = MASTER_LEAGUES[k];
    if (v === null || v === undefined || conteggio[v] > 1) delete MASTER_LEAGUES[k];
  }
  for (const n of ['🇫🇮 Finnish Cup', '🇳🇴 Norwegian Cup', '🇸🇪 Svenska Cupen', '🇩🇰 DBU Pokalen']) LEGHE_ANNO_SOLARE.add(n);
  try { localStorage.setItem(CHIAVE_LS, JSON.stringify({ ts: Date.now(), map: MASTER_LEAGUES })); } catch (e) { /* ok */ }
}

// ── utilità ─────────────────────────────────────────────────────────────────
const fmtOrarioIta = new Intl.DateTimeFormat('it-IT', {
  timeZone: 'Europe/Rome', day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
});
function orarioIta(date) {
  const p = Object.fromEntries(fmtOrarioIta.formatToParts(date).map(x => [x.type, x.value]));
  return `${p.day}/${p.month} ${p.hour}:${p.minute}`;
}

async function conConcorrenza(items, n, fn) {
  const out = new Array(items.length);
  let i = 0;
  await Promise.all(Array.from({ length: Math.min(n, items.length) }, async () => {
    while (i < items.length) { const k = i++; out[k] = await fn(items[k], k); }
  }));
  return out;
}

const SQUADRA_VUOTA = (id) => ({ id, rank: 10, giocate: 0, punti: 0, ac: 0.0, dc: 0.0, at: 0.0, dt: 0.0 });

// ── analisi di una singola partita ──────────────────────────────────────────
async function analizzaPartita(ctx, f) {
  const { name, fId, isCoppaEu, isCoppaNaz, isCoppa, isPlayoff, isLegaCieca, stagioneLega, dbStats,
          puntiChampions, puntiSalvezza, totSquadre, partiteTotCamp, oddsCache, meseAtt } = ctx;
  const fixId = f.fixture.id;
  const matchDateStr = f.fixture.date.slice(0, 10);
  const matchTime = new Date(f.fixture.date);
  const orario = orarioIta(matchTime);
  const cU = f.teams.home.name; const tU = f.teams.away.name;
  const cS = semplificaNome(cU); const tS = semplificaNome(tU);
  const quoteRealiMatch = (oddsCache[matchDateStr] ?? {})[fixId] ?? {};

  for (const [sn, tid] of [[cS, f.teams.home.id], [tS, f.teams.away.id]]) {
    if (!dbStats[sn]) dbStats[sn] = SQUADRA_VUOTA(tid);
  }
  const cId = dbStats[cS].id; const tId = dbStats[tS].id;
  const citta = f.fixture.venue?.city || cS;

  const [sqC, sqT, stagC, stagT, meteo, h2h, legaC, legaT, avzC, avzT] = await Promise.all([
    analizzaSquadraGlobale(cId), analizzaSquadraGlobale(tId),
    analizzaStatisticheStagionali(fId, cId, stagioneLega), analizzaStatisticheStagionali(fId, tId, stagioneLega),
    scaricaMeteo(citta), analizzaH2hDnaEAndata(cId, tId),
    trovaLegaSquadra(cId, stagioneLega, fId), trovaLegaSquadra(tId, stagioneLega, fId),
    analizzaStatisticheAvanzatePro(cId), analizzaStatisticheAvanzatePro(tId),
  ]);
  const [mMet, dMet] = meteo;
  let { boostC: bAndC, boostT: bAndT, andataMsg } = h2h;
  const { mH2hC, mH2hT, golC: golH2hC, golT: golH2hT, storico: strH2h, dettagli: detH2h } = h2h;
  const { cs: csC, fts: ftsC } = stagC; const { cs: csT, fts: ftsT } = stagT;

  const ctxSpar = await rilevaContestoSpareggio(fixId, cId, tId, legaC, legaT, matchDateStr);
  if (ctxSpar.isRitorno || ctxSpar.isInterlega) {
    bAndC *= ctxSpar.boostC; bAndT *= ctxSpar.boostT;
    if (ctxSpar.msg) andataMsg = ctxSpar.msg;
  }
  const pesoMomOverride = ctxSpar.isInterlega ? ctxSpar.pesoMomentum : null;

  const { poss: possC, box: boxC, conv: convC, corn: cornC, cart: cartC, falli: falliC, par: parC,
          stile: stileC, sqCerti: sqCertC, rig: rigC, gfHome: gfHomeC, gsHome: gsHomeC } = avzC;
  const { poss: possT, box: boxT, conv: convT, corn: cornT, cart: cartT, falli: falliT, par: parT,
          stile: stileT, sqCerti: sqCertT, rig: rigT, gfAway: gfAwayT, gsAway: gsAwayT } = avzT;
  const tiriC = avzC.tiri; const tiriT = avzT.tiri;

  // Affidabilità dinamica
  const nDegradati = [sqC.ok, sqT.ok, stagC.ok, stagT.ok, h2h.ok, avzC.ok, avzT.ok].filter(ok => !ok).length;
  const affBase = getAffidabilita(name);
  let affMatch;
  if (nDegradati >= 4) affMatch = 'BASSA';
  else if (nDegradati >= 1) affMatch = { 3: 'ALTA', 2: 'MEDIA', 1: 'BASSA' }[Math.max(1, AFFIDABILITA_ORDINE[affBase] - 1)];
  else affMatch = affBase;

  const msgRadar = isLegaCieca ? '⚠️ Radar Infortuni Offline (Lega Minore)' : '';
  let malusAttC = 0, boostOppC = 0, malusAttT = 0, boostOppT = 0;
  let t1C = 0, t2C = 0, t3C = 0, countC = 0, sqCnt_C = 0, defOutC = 0, gkOutC = false;
  let t1T = 0, t2T = 0, t3T = 0, countT = 0, sqCnt_T = 0, defOutT = 0, gkOutT = false;

  if (isLegaCieca) {
    if (sqCertC > 0) { sqCnt_C += sqCertC; countC += sqCertC; malusAttC += 0.05 * sqCertC; }
    if (sqCertT > 0) { sqCnt_T += sqCertT; countT += sqCertT; malusAttT += 0.05 * sqCertT; }
  } else {
    const inj = await apiGet('injuries', { fixture: fixId }, { ttl: 1800, timeoutMs: 10000 });
    let infAll = Array.isArray(inj.response) ? [...inj.response] : [];
    if (infAll.length === 0) {
      const [ic, it] = await Promise.all([
        apiGet('injuries', { team: cId, date: matchDateStr }, { ttl: 1800, timeoutMs: 10000 }),
        apiGet('injuries', { team: tId, date: matchDateStr }, { ttl: 1800, timeoutMs: 10000 }),
      ]);
      if (Array.isArray(ic.response)) infAll.push(...ic.response);
      if (Array.isArray(it.response)) infAll.push(...it.response);
    }
    const infC = infAll.filter(i => String(i.team.id) === String(cId));
    const infT = infAll.filter(i => String(i.team.id) === String(tId));
    const [rC, rT] = await Promise.all([
      analizzaInfortuniPesatiV90(infC, stagioneLega), analizzaInfortuniPesatiV90(infT, stagioneLega)]);
    ({ malusAtt: malusAttC, boostOpp: boostOppC, t1: t1C, t2: t2C, t3: t3C, count: countC, sq: sqCnt_C, gkOut: gkOutC, defOut: defOutC } = rC);
    ({ malusAtt: malusAttT, boostOpp: boostOppT, t1: t1T, t2: t2T, t3: t3T, count: countT, sq: sqCnt_T, gkOut: gkOutT, defOut: defOutT } = rT);
    if (sqCertC > 0 && sqCnt_C === 0) { sqCnt_C += sqCertC; countC += sqCertC; malusAttC += 0.05 * sqCertC; }
    if (sqCertT > 0 && sqCnt_T === 0) { sqCnt_T += sqCertT; countT += sqCertT; malusAttT += 0.05 * sqCertT; }
  }

  // Squad Depth Buffer
  if (!isCoppa) {
    const gapC = (dbStats[cS].punti || 0) - (dbStats[tS].punti || 0);
    const gapT = -gapC;
    if (gapC >= 15) { const a = Math.max(0.20, 1.0 - gapC / 45.0); malusAttC *= a; boostOppT *= a; }
    else if (gapT >= 15) { const a = Math.max(0.20, 1.0 - gapT / 45.0); malusAttT *= a; boostOppC *= a; }
  }

  const streakBreakC = (golH2hC === 0) && (countT > 0 || sqT.isStanca);
  const streakBreakT = (golH2hT === 0) && (countC > 0 || sqC.isStanca);

  // Motivazione + pressione
  let mMotC = 1.0, mMotT = 1.0, pressioneC = 0.0, pressioneT = 0.0;
  let msgMot = ''; let msgPressione = '';
  const formaC = sqC.forma; const formaT = sqT.forma;

  if (isCoppaNaz) { mMotC = mMotT = 1.20; msgMot = '🏆 COPPA NAZIONALE'; }
  else if (isCoppaEu && [3, 4, 5].includes(meseAtt)) { mMotC = mMotT = 1.25; msgMot = '🔥 DENTRO O FUORI'; }
  else if (isCoppaEu) { mMotC = mMotT = 1.15; msgMot = '🇪🇺 Coppa Europea'; }
  else if (isPlayoff) { mMotC = mMotT = 1.30; msgMot = '⚡ PLAYOFF'; }
  else if (!isCoppa) {
    const puntiC = dbStats[cS].punti || 0; const puntiT = dbStats[tS].punti || 0;
    const rankC = dbStats[cS].rank ?? 10; const rankT = dbStats[tS].rank ?? 10;
    const giocC = dbStats[cS].giocate || 0; const giocT = dbStats[tS].giocate || 0;
    const gapChC = puntiChampions - puntiC; const gapChT = puntiChampions - puntiT;
    const partRimC = Math.max(1, partiteTotCamp - giocC); const partRimT = Math.max(1, partiteTotCamp - giocT);
    const maxRagC = puntiC + partRimC * 3; const maxRagT = puntiT + partRimT * 3;

    if (maxRagC < puntiSalvezza) { mMotC = 0.75; msgMot += '💀 C.Retrocessa '; }
    else if (puntiC > puntiSalvezza + partRimC * 2) { mMotC = 0.85; msgMot += '🏖️ C.Salva '; }
    else if (puntiC >= puntiChampions) { mMotC = 1.20; msgMot += '🏆 C.InChampions '; }
    else if (0 < gapChC && gapChC <= partRimC * 2) {
      const urgenza = 1.0 - (gapChC / (partRimC * 3)); mMotC = 1.10 + urgenza * 0.20; msgMot += '🔥 C.CorsaChamp ';
    } else if (rankC >= totSquadre - 3) { mMotC = 1.25; msgMot += '🆘 C.Disperata '; }
    else if (rankC >= totSquadre - 6) { mMotC = 1.15; msgMot += '😰 C.ARischio '; }
    else mMotC = 1.05;

    if (maxRagT < puntiSalvezza) { mMotT = 0.75; msgMot += '💀 O.Retrocessa'; }
    else if (puntiT > puntiSalvezza + partRimT * 2) { mMotT = 0.85; msgMot += '🏖️ O.Salva'; }
    else if (puntiT >= puntiChampions) { mMotT = 1.20; msgMot += '🏆 O.InChampions'; }
    else if (0 < gapChT && gapChT <= partRimT * 2) {
      const urgenza = 1.0 - (gapChT / (partRimT * 3)); mMotT = 1.10 + urgenza * 0.20; msgMot += '🔥 O.CorsaChamp';
    } else if (rankT >= totSquadre - 3) { mMotT = 1.25; msgMot += '🆘 O.Disperata'; }
    else if (rankT >= totSquadre - 6) { mMotT = 1.15; msgMot += '😰 O.ARischio'; }
    else mMotT = 1.05;

    if (Math.abs(rankC - rankT) <= 2) msgMot += ' ⚔️ScontroDiretto';

    const conta = (s, ch) => s.split(ch).length - 1;
    const sconfC = conta(formaC, 'L'); const trendC = sqC.punti5 - sqC.puntiPrev5;
    if (mMotC >= 1.15) pressioneC += 0.10;
    if (sconfC >= 4) pressioneC += 0.20; else if (sconfC >= 3) pressioneC += 0.12; else if (sconfC >= 2) pressioneC += 0.06;
    if (trendC <= -6) pressioneC += 0.10; else if (trendC <= -3) pressioneC += 0.05;
    pressioneC = Math.min(0.35, pressioneC);

    const sconfT = conta(formaT, 'L'); const trendT = sqT.punti5 - sqT.puntiPrev5;
    if (mMotT >= 1.15) pressioneT += 0.10;
    if (sconfT >= 4) pressioneT += 0.20; else if (sconfT >= 3) pressioneT += 0.12; else if (sconfT >= 2) pressioneT += 0.06;
    if (trendT <= -6) pressioneT += 0.10; else if (trendT <= -3) pressioneT += 0.05;
    pressioneT = Math.min(0.35, pressioneT);

    if (mMotC <= 0.90) mMotC *= conta(formaC, 'W') >= 3 ? 1.12 : 1.05;
    if (mMotT <= 0.90) mMotT *= conta(formaT, 'W') >= 3 ? 1.12 : 1.05;

    if (pressioneC > 0.15) msgPressione += ` 😬Pressione Casa:${(pressioneC * 100).toFixed(0)}%`;
    if (pressioneT > 0.15) msgPressione += ` 😬Pressione Osp:${(pressioneT * 100).toFixed(0)}%`;
  }
  mMotC *= (1 - pressioneC); mMotT *= (1 - pressioneT);

  // Hybrid xG
  const xgStC = Math.sqrt(Math.max(0.01, dbStats[cS].ac || 0.0) * Math.max(0.01, dbStats[tS].dt || 0.0));
  const xgStT = Math.sqrt(Math.max(0.01, dbStats[tS].at || 0.0) * Math.max(0.01, dbStats[cS].dc || 0.0));
  const xgMoC = Math.sqrt(Math.max(0.01, gfHomeC) * Math.max(0.01, gsHomeT_(avzT)));
  const xgMoT = Math.sqrt(Math.max(0.01, gfAwayT) * Math.max(0.01, gsAwayC_(avzC)));
  let pesoMom;
  if (pesoMomOverride !== null) pesoMom = pesoMomOverride;
  else if (isCoppa || isPlayoff || (dbStats[cS].giocate || 0) <= 5) pesoMom = 0.80;
  else pesoMom = 0.30;
  const pesoStd = 1.0 - pesoMom;
  const stimaInstabile = pesoMom > 0.30;
  let xgBaseC = ((xgStC * pesoStd) + (xgMoC * pesoMom)) * sqC.mForma * sqC.mStanchezza;
  let xgBaseT = ((xgStT * pesoStd) + (xgMoT * pesoMom)) * sqT.mForma * sqT.mStanchezza;

  const malLega = ['🇬🇷 Super League', '🇫🇷 Ligue 1', '🇮🇹 Serie B'].includes(name) ? 0.85 : 1.0;
  xgBaseC *= malLega; xgBaseT *= malLega;
  if (convC < 3.0) xgBaseC *= 1.15; else if (convC > 7.0) xgBaseC *= 0.85;
  if (convT < 3.0) xgBaseT *= 1.15; else if (convT > 7.0) xgBaseT *= 0.85;
  xgBaseC *= Math.min(1.20, 1.0 + (boxC / 15.0) * 0.15);
  xgBaseT *= Math.min(1.20, 1.0 + (boxT / 15.0) * 0.15);
  xgBaseC *= (1 - Math.min(0.25, (parC / 6.0) * 0.20));
  xgBaseT *= (1 - Math.min(0.25, (parT / 6.0) * 0.20));

  const totFalli = falliC + falliT;
  if (totFalli > 28) { xgBaseC *= 0.90; xgBaseT *= 0.90; }
  if (ftsC > 35) xgBaseC *= 0.85;
  if (csT > 35) xgBaseC *= 0.85;
  if (ftsT > 35) xgBaseT *= 0.85;
  if (csC > 35) xgBaseT *= 0.85;

  const sgC = msgMot.includes('C.Salva'); const sgT = msgMot.includes('O.Salva');
  let xgC = xgBaseC * (1 - malusAttC) * (1 + boostOppT) * mH2hC * bAndC * mMotC * (sgT ? 1.10 : 1.0);
  let xgT = xgBaseT * (1 - malusAttT) * (1 + boostOppC) * mH2hT * bAndT * mMotT * (sgC ? 1.10 : 1.0);

  let msgStreak = '';
  if (streakBreakC) { xgC *= 1.45; msgStreak += '🔥 STREAK CASA '; }
  if (streakBreakT) { xgT *= 1.45; msgStreak += '🔥 STREAK OSPITE'; }
  xgC *= mMet; xgT *= mMet;

  const arb = f.fixture.referee || 'N/D';
  const isSev = ['Orsato', 'Maresca', 'Taylor', 'Oliver', 'Lahoz', 'Hernandez'].some(s => String(arb).includes(s));
  if (isSev) { xgC *= 1.05; xgT *= 1.05; }
  xgC = Math.min(XG_MAX, Math.max(XG_MIN, xgC));
  xgT = Math.min(XG_MAX, Math.max(XG_MIN, xgT));

  const avgCorn = cornC + cornT; const avgCart = cartC + cartT;
  let fullTips = calcolaTuttiIMercati(xgC, xgT, avgCorn, avgCart, isSev, totFalli);
  fullTips = applicaBlendMercato1x2(fullTips, quoteRealiMatch, stimaInstabile ? 0.55 : 0.15);

  let bestKey = '1';
  for (const k of ['1', 'X', '2']) if (fullTips.get(k) > fullTips.get(bestKey)) bestKey = k;
  let bestProb, bestQ, bestReal;
  if (fullTips.get(bestKey) < 45.0) { bestKey = 'No Segno Fisso'; bestProb = 0.0; bestQ = '-'; bestReal = false; }
  else { bestProb = fullTips.get(bestKey); [bestQ, bestReal] = getQuotaFinale(bestKey, bestProb, quoteRealiMatch); }

  const SOGLIA_EDGE_SOSPETTO = 60.0;
  const tips = [];
  for (const [k, v] of fullTips) {
    const [qFin, isReal] = getQuotaFinale(k, v, quoteRealiMatch);
    const edgeV = calcolaEdgePct(v, qFin);
    if (stimaInstabile && edgeV > SOGLIA_EDGE_SOSPETTO) continue;
    tips.push({
      Match: `${cU} vs ${tU}`, League: name, Tip: k, Prob: v, Quota: qFin, Real: isReal, Time: orario,
      Edge: edgeV, Kelly: kellyFraction(v, qFin), Aff: affMatch, Instabile: stimaInstabile, FixtureID: fixId,
    });
  }

  const match = {
    orario, ts: matchTime.getTime(), c_u: cU, t_u: tU, c_s: cS, t_s: tS, fixture_id: fixId,
    rank_c: dbStats[cS].rank ?? 10, rank_t: dbStats[tS].rank ?? 10,
    cs_c: csC, fts_c: ftsC, cs_t: csT, fts_t: ftsT,
    all_tips: fullTips, best_1x2: [bestKey, bestProb, bestQ, bestReal], quote_reali: quoteRealiMatch,
    xg_c: xgC, xg_t: xgT, arb, is_sev: isSev,
    count_c: countC, sq_c: sqCnt_C, t1_c: t1C, t2_c: t2C, t3_c: t3C, gk_out_c: gkOutC, def_out_c: defOutC,
    count_t: countT, sq_t: sqCnt_T, t1_t: t1T, t2_t: t2T, t3_t: t3T, gk_out_t: gkOutT, def_out_t: defOutT,
    meteo: dMet, msg_radar: msgRadar, dna_h2h: strH2h, dettagli_h2h: detH2h,
    streak_msg: msgStreak.trim(), andata_msg: andataMsg, msg_mot: msgMot.trim(),
    stan_c: sqC.isStanca ? '⚠️ Fatigue' : '✅ Riposo', stan_t: sqT.isStanca ? '⚠️ Fatigue' : '✅ Riposo',
    forma_c: formaC, forma_t: formaT, rit_c: sqC.ritardi, rit_t: sqT.ritardi,
    pressione_c: pressioneC, pressione_t: pressioneT, msg_pressione: msgPressione,
    poss_c: possC, tiri_c: tiriC, conv_c: convC, stile_c: stileC, box_c: boxC, falli_c: falliC, parate_c: parC, rig_c: rigC,
    gf_home_c: gfHomeC, gs_home_c: gsHomeC,
    poss_t: possT, tiri_t: tiriT, conv_t: convT, stile_t: stileT, box_t: boxT, falli_t: falliT, parate_t: parT, rig_t: rigT,
    gf_away_t: gfAwayT, gs_away_t: gsAwayT,
    corn_tot: avgCorn, cart_tot: avgCart, falli_tot: totFalli, aff_dinamica: affMatch, n_degradati: nDegradati,
  };
  return { match, tips };
}
// piccoli accessor (leggibilità): gol subiti in casa dell'avversario ecc.
function gsHomeT_(avzT) { return avzT.gsHome; }
function gsAwayC_(avzC) { return avzC.gsAway; }

// ── estrazione principale ───────────────────────────────────────────────────
// Python: xg_mo_c = sqrt(gf_home_c * gs_home_t); xg_mo_t = sqrt(gf_away_t * gs_away_c).
export async function estraiMatrix({ scelte, activeDict, startStr, endStr, onProgresso = () => {}, onAvviso = () => {} }) {
  const dataMaster = new Map();
  const allTips = [];
  const nowUtc = new Date();
  const meseAtt = new Date().getMonth() + 1;
  const stagione = stagioneCorrente();
  const annoStart = parseInt(startStr.slice(0, 4), 10);
  const totLeghe = scelte.length;

  for (let idx = 0; idx < scelte.length; idx++) {
    const name = scelte[idx];
    onProgresso(idx + 1, totLeghe, name);
    const fId = activeDict[name];
    const isCoppaEu = COPPE_EUROPEE.has(name);
    const isCoppaNaz = COPPE_NAZIONALI.has(name);
    const stagioneLega = LEGHE_ANNO_SOLARE.has(name) ? annoStart : stagione;
    const base = {
      name, fId, isCoppaEu, isCoppaNaz, isCoppa: isCoppaEu || isCoppaNaz, isPlayoff: LEGHE_PLAYOFF.has(name),
      isLegaCieca: LEGHE_CIECHE.has(fId), stagioneLega, meseAtt,
    };
    try {
      const fix = await apiGet('fixtures', { league: fId, season: stagioneLega, from: startStr, to: endStr }, { ttl: 600, timeoutMs: 15000 });
      if (!fix.response?.length) continue;

      const dbStats = {};
      let puntiChampions = 0, puntiSalvezza = 0, totSquadre = 20, partiteTotCamp = 38;
      const std = await apiGet('standings', { league: fId, season: stagioneLega }, { ttl: 3600, timeoutMs: 15000 });
      if (std.response?.length && std.response[0].league?.standings) {
        for (const gruppo of std.response[0].league.standings) {
          totSquadre = gruppo.length;
          partiteTotCamp = Math.max((totSquadre - 1) * 2, 38);
          if (totSquadre >= 4) {
            puntiChampions = gruppo[3].points || 0;
            puntiSalvezza = gruppo[totSquadre - 4].points || 0;
          }
          for (const t of gruppo) {
            dbStats[semplificaNome(t.team.name)] = {
              id: t.team.id, rank: t.rank || 10, giocate: t.all.played || 0, punti: t.points || 0,
              ac: (t.home.goals.for || 0) / Math.max(1, t.home.played || 1),
              dc: (t.home.goals.against || 0) / Math.max(1, t.home.played || 1),
              at: (t.away.goals.for || 0) / Math.max(1, t.away.played || 1),
              dt: (t.away.goals.against || 0) / Math.max(1, t.away.played || 1),
            };
          }
        }
      } else {
        for (const f of fix.response) for (const tt of ['home', 'away']) {
          const n = semplificaNome(f.teams[tt].name);
          if (!dbStats[n]) dbStats[n] = SQUADRA_VUOTA(f.teams[tt].id);
        }
      }

      // Prior stagione precedente
      const prev = await scaricaStandingsPregressi(fId, parseInt(stagioneLega, 10) - 1);
      if (Object.keys(prev).length) {
        for (const st of Object.values(dbStats)) {
          const p = prev[st.id];
          if (!p) continue;
          const g = st.giocate || 0;
          for (const campo of ['ac', 'dc', 'at', 'dt']) st[campo] = blendPriorStagione(st[campo], p[campo], g);
        }
      }

      // Quote
      const date = [...new Set(fix.response.map(f => f.fixture.date.slice(0, 10)))];
      const oddsCache = {};
      const quote = await Promise.all(date.map(d => scaricaQuoteNative(fId, d, stagioneLega)));
      date.forEach((d, i) => { oddsCache[d] = quote[i]; });

      const daFare = fix.response.filter(f =>
        !['PST', 'CANC', 'ABD', 'AWD', 'WO'].includes(f.fixture.status.short)
        && new Date(f.fixture.date) > nowUtc);
      const ctx = { ...base, dbStats, puntiChampions, puntiSalvezza, totSquadre, partiteTotCamp, oddsCache };

      const risultati = await conConcorrenza(daFare, 3, async f => {
        try { return await analizzaPartita(ctx, f); }
        catch (e) {
          if (e instanceof ErroreAutenticazione) throw e;
          onAvviso(`⚠️ ${name}: salto ${f.teams.home.name} vs ${f.teams.away.name} (${e.message})`);
          return null;
        }
      });
      const matchesList = [];
      for (const r of risultati) { if (r) { matchesList.push(r.match); allTips.push(...r.tips); } }
      if (matchesList.length) dataMaster.set(name, matchesList);
    } catch (e) {
      if (e instanceof ErroreAutenticazione) throw e;
      onAvviso(`⚠️ Errore durante l'analisi di ${name}: ${e.message} — salto questo campionato e continuo con gli altri.`);
    }
  }
  return { dataMaster, allTips };
}
