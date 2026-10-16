// api.js — accesso ad API-Football tramite il proxy /api (Cloud Function):
// la chiave non è mai nel browser. Port di matrix_api.py, con cache in
// memoria (stessi TTL di st.cache_data) e concorrenza limitata.
import { FREQUENZE_MEDIE, N_PARTITE_STATS_AVANZATE } from './leghe.js';

let _tokenProvider = async () => null;
export function impostaTokenProvider(fn) { _tokenProvider = fn; }

export class ErroreAutenticazione extends Error {}

const cacheMem = new Map();   // chiave -> { scade, dati }
const inVolo = new Map();     // chiave -> Promise
const MAX_CONCORRENTI = 6;
let attive = 0;
const codaAttesa = [];
let contatoreChiamate = 0;
export const statistiche = { get chiamate() { return contatoreChiamate; } };

function acquisisci() {
  if (attive < MAX_CONCORRENTI) { attive++; return Promise.resolve(); }
  return new Promise(res => codaAttesa.push(res));
}
function rilascia() {
  const next = codaAttesa.shift();
  if (next) next(); else attive--;
}
const attendi = ms => new Promise(r => setTimeout(r, ms));

export function svuotaCacheApi() { cacheMem.clear(); }

async function richiesta(url, timeoutMs) {
  let ultimoErrore;
  for (let tentativo = 0; tentativo < 3; tentativo++) {
    await acquisisci();
    try {
      const token = await _tokenProvider();
      if (!token) throw new ErroreAutenticazione('Non autenticato');
      const ac = new AbortController();
      const t = setTimeout(() => ac.abort(), timeoutMs);
      contatoreChiamate++;
      let r;
      try { r = await fetch(url, { headers: { Authorization: `Bearer ${token}` }, signal: ac.signal }); }
      finally { clearTimeout(t); }
      if (r.status === 401) throw new ErroreAutenticazione('Sessione scaduta o account non autorizzato');
      if (r.status === 429 || r.status >= 500) { ultimoErrore = new Error(`HTTP ${r.status}`); }
      else return await r.json();
    } catch (e) {
      if (e instanceof ErroreAutenticazione) throw e;
      ultimoErrore = e;
    } finally { rilascia(); }
    await attendi(700 * 2 ** tentativo);
  }
  throw ultimoErrore ?? new Error('Richiesta fallita');
}

// ttl in secondi: cache lato client E lato proxy. 0 = nessuna cache.
export async function apiGet(endpoint, params = {}, { ttl = 0, timeoutMs = 20000 } = {}) {
  const qs = new URLSearchParams();
  for (const k of Object.keys(params).sort()) if (params[k] !== undefined && params[k] !== null) qs.set(k, String(params[k]));
  const chiave = `${endpoint}?${qs.toString()}`;
  const ora = Date.now();
  if (ttl > 0) {
    const hit = cacheMem.get(chiave);
    if (hit && hit.scade > ora) return hit.dati;
    if (inVolo.has(chiave)) return inVolo.get(chiave);
  }
  if (ttl > 0) qs.set('ttl', String(ttl));
  const p = richiesta(`/api/${endpoint}${qs.toString() ? '?' + qs.toString() : ''}`, timeoutMs)
    .then(dati => { if (ttl > 0) cacheMem.set(chiave, { scade: Date.now() + ttl * 1000, dati }); return dati; })
    .finally(() => inVolo.delete(chiave));
  if (ttl > 0) inVolo.set(chiave, p);
  return p;
}

// ── utilità data ────────────────────────────────────────────────────────────
const pad = n => String(n).padStart(2, '0');
export const fmtData = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
export function parseData(s) { const [y, m, d] = s.slice(0, 10).split('-').map(Number); return new Date(y, m - 1, d); }
export function aggiungiGiorni(d, n) { const x = new Date(d); x.setDate(x.getDate() + n); return x; }
const giorniDa = (data) => Math.floor((Date.now() - data.getTime()) / 86400000);
const toInt = v => { const n = parseInt(v ?? 0, 10); return Number.isFinite(n) ? n : 0; };

// ── auto-discovery ID ───────────────────────────────────────────────────────
export async function trovaVeroIdLega(nazione, nome, fallbackId) {
  try {
    const r = await apiGet('leagues', { country: nazione, name: nome }, { ttl: 86400, timeoutMs: 8000 });
    if (r.response?.length) return r.response[0].league.id;
  } catch (e) { /* fallback */ }
  return fallbackId;
}

export async function trovaIdMultipli(nazione, fallbackMap) {
  try {
    const r = await apiGet('leagues', { country: nazione, type: 'League' }, { ttl: 86400, timeoutMs: 8000 });
    const out = {};
    for (const e of r.response ?? []) out[e.league.name] = e.league.id;
    return Object.keys(out).length ? out : fallbackMap;
  } catch (e) { return fallbackMap; }
}

export async function risolviIdPerNome(nazione, chiaveNome, fallbackId) {
  const leghe = await trovaIdMultipli(nazione, {});
  for (const [nome, id] of Object.entries(leghe)) if (nome.toLowerCase().includes(chiaveNome.toLowerCase())) return id;
  return fallbackId;
}

export async function trovaIdCoppa(nazione, nomeCoppa, fallbackId) {
  try {
    const r = await apiGet('leagues', { country: nazione, name: nomeCoppa, type: 'Cup' }, { ttl: 86400, timeoutMs: 8000 });
    if (r.response?.length) return r.response[0].league.id;
  } catch (e) { /* fallback */ }
  return fallbackId;
}

export async function getActiveLeagues(startStr, endStr, masterLeagues) {
  const start = parseData(startStr); const end = parseData(endStr);
  const giorni = Math.min(Math.round((end - start) / 86400000) + 1, 7);
  try {
    const ids = new Set();
    const risposte = await Promise.all(Array.from({ length: giorni }, (_, i) =>
      apiGet('fixtures', { date: fmtData(aggiungiGiorni(start, i)) }, { ttl: 3600, timeoutMs: 15000 })));
    for (const r of risposte) for (const f of r.response ?? []) ids.add(f.league.id);
    return Object.fromEntries(Object.entries(masterLeagues).filter(([, v]) => ids.has(v)));
  } catch (e) { return masterLeagues; }
}

// ── giocatori / infortuni ───────────────────────────────────────────────────
export async function getPlayerAdvancedStats(playerId, season) {
  const vuoto = { pos: 'Unknown', gol: 0, assist: 0, rating: 6.0, mins: 0 };
  if (!playerId) return vuoto;
  try {
    const r = await apiGet('players', { id: playerId, season }, { ttl: 86400, timeoutMs: 10000 });
    let pos = 'Unknown'; let mins = 0; let gol = 0; let assist = 0; const ratings = [];
    for (const st of (r.response?.[0]?.statistics) ?? []) {
      if (pos === 'Unknown' && st.games?.position) pos = st.games.position;
      mins += st.games?.minutes || 0;
      gol += st.goals?.total || 0;
      assist += st.goals?.assists || 0;
      if (st.games?.rating) ratings.push(parseFloat(st.games.rating));
    }
    const rating = ratings.length ? ratings.reduce((a, b) => a + b, 0) / ratings.length : 6.0;
    return { pos, gol, assist, rating, mins };
  } catch (e) { return vuoto; }
}

export async function analizzaInfortuniPesatiV90(infList, seasonLega) {
  let malusAtt = 0.0; let boostOpp = 0.0;
  let t1Star = 0, t2Rot = 0, t3Ris = 0, squalificati = 0, difensoriOut = 0;
  let portiereTitolareOut = false;
  const visti = new Set();
  const daAnalizzare = [];
  for (const i of infList) {
    const pId = i.player?.id;
    if (!pId || visti.has(pId)) continue;
    visti.add(pId);
    daAnalizzare.push(i);
  }
  const statsTutti = await Promise.all(daAnalizzare.map(i => getPlayerAdvancedStats(i.player.id, seasonLega)));
  daAnalizzare.forEach((i, idx) => {
    const motivo = String(i.type ?? '').toLowerCase();
    if (motivo.includes('suspend') || motivo.includes('red card') || motivo.includes('card')) squalificati++;
    const { pos, gol, assist, rating, mins } = statsTutti[idx];
    const isStar = mins >= 1200 || rating >= 7.0;
    if (isStar) t1Star++; else if (mins >= 400) t2Rot++; else t3Ris++;
    if (gol >= 5 || assist >= 5 || (['Attacker', 'Midfielder'].includes(pos) && isStar)) {
      malusAtt += 0.15;
      if (gol >= 10) malusAtt += 0.10;
      if (assist >= 8) malusAtt += 0.10;
      if (rating >= 7.3) malusAtt += 0.10;
    }
    if (pos === 'Defender') {
      if (isStar) { boostOpp += 0.15; difensoriOut++; }
      else if (mins >= 400) { boostOpp += 0.05; difensoriOut++; }
    } else if (pos === 'Goalkeeper' && isStar) { portiereTitolareOut = true; boostOpp += 0.25; }
  });
  if (difensoriOut >= 2) boostOpp += 0.20;
  return {
    malusAtt: Math.min(0.60, malusAtt), boostOpp: Math.min(0.60, boostOpp),
    t1: t1Star, t2: t2Rot, t3: t3Ris, count: visti.size, sq: squalificati,
    gkOut: portiereTitolareOut, defOut: difensoriOut,
  };
}

// ── quote ───────────────────────────────────────────────────────────────────
export async function scaricaQuoteNative(leagueId, dateStr, seasonLega) {
  try {
    const r = await apiGet('odds', { league: leagueId, season: seasonLega, date: dateStr, bookmaker: 8 }, { ttl: 3600, timeoutMs: 10000 });
    const qd = {};
    for (const item of r.response ?? []) {
      const fid = item.fixture.id;
      const q = qd[fid] = {};
      if (item.bookmakers?.length) {
        for (const bet of item.bookmakers[0].bets) {
          if (bet.id === 1) {
            for (const v of bet.values) {
              if (v.value === 'Home') q['1'] = parseFloat(v.odd);
              else if (v.value === 'Draw') q['X'] = parseFloat(v.odd);
              else if (v.value === 'Away') q['2'] = parseFloat(v.odd);
            }
          } else if (bet.id === 5) {
            for (const v of bet.values) {
              const lbl = v.value;
              if (lbl.includes('Over')) q[`O${lbl.split(' ')[1]}`] = parseFloat(v.odd);
              else if (lbl.includes('Under')) q[`U${lbl.split(' ')[1]}`] = parseFloat(v.odd);
            }
          } else if (bet.id === 12) {
            for (const v of bet.values) {
              if (v.value === 'Home/Draw') q['1X'] = parseFloat(v.odd);
              else if (v.value === 'Draw/Away') q['X2'] = parseFloat(v.odd);
              else if (v.value === 'Home/Away') q['12'] = parseFloat(v.odd);
            }
          } else if (bet.id === 6) {
            for (const v of bet.values) {
              if (v.value === 'Yes') q['Goal'] = parseFloat(v.odd);
              else if (v.value === 'No') q['NoGoal'] = parseFloat(v.odd);
            }
          }
        }
      }
    }
    return qd;
  } catch (e) { return {}; }
}

// ── statistiche squadra ─────────────────────────────────────────────────────
export async function analizzaStatisticheStagionali(leagueId, teamId, seasonLega) {
  try {
    const r = await apiGet('teams/statistics', { league: leagueId, season: seasonLega, team: teamId }, { ttl: 86400, timeoutMs: 10000 });
    const stats = r.response;
    if (!stats || Array.isArray(stats) || !Object.keys(stats).length) return { cs: 0.0, fts: 0.0, ok: true };
    const giocate = stats.fixtures?.played?.total ?? 0;
    if (giocate === 0) return { cs: 0.0, fts: 0.0, ok: true };
    const cs = Math.min(85.0, ((stats.clean_sheet?.total ?? 0) / giocate) * 100);
    const fts = Math.min(85.0, ((stats.failed_to_score?.total ?? 0) / giocate) * 100);
    return { cs, fts, ok: true };
  } catch (e) { return { cs: 0.0, fts: 0.0, ok: false }; }
}

export async function scaricaStandingsPregressi(leagueId, season) {
  try {
    const r = await apiGet('standings', { league: leagueId, season }, { ttl: 604800, timeoutMs: 12000 });
    const out = {};
    if (!r.response?.length) return out;
    for (const gruppo of r.response[0].league.standings) {
      for (const t of gruppo) {
        out[t.team.id] = {
          ac: (t.home.goals.for || 0) / Math.max(1, t.home.played || 1),
          dc: (t.home.goals.against || 0) / Math.max(1, t.home.played || 1),
          at: (t.away.goals.for || 0) / Math.max(1, t.away.played || 1),
          dt: (t.away.goals.against || 0) / Math.max(1, t.away.played || 1),
        };
      }
    }
    return out;
  } catch (e) { return {}; }
}

export async function analizzaStatisticheAvanzatePro(teamId) {
  const fallback = {
    poss: 50.0, tiri: 4.0, box: 5.0, conv: 5.0, corn: 4.5, cart: 2.0, falli: 10.0, par: 2.5,
    stile: 'Bilanciato', sqCerti: 0, gf10: 1.0, gs10: 1.0, rig: 0.0,
    gfHome: 1.0, gsHome: 1.0, gfAway: 1.0, gsAway: 1.0, ok: false,
  };
  try {
    const r = await apiGet('fixtures', { team: teamId, last: 10, status: 'FT' }, { ttl: 1800, timeoutMs: 12000 });
    const matches = r.response ?? [];
    let totPoss = 0, totTiri = 0, totArea = 0, totGf = 0, totGs = 0;
    let totCorn = 0, totCart = 0, totFalli = 0, totPar = 0, totRigori = 0;
    let mvStats = 0, mvGoals = 0, sqCerti = 0;
    let gfHome = 0, gsHome = 0, nHome = 0, gfAway = 0, gsAway = 0, nAway = 0;

    const richieste = matches.map((m, i) => {
      const fid = m.fixture.id;
      const ev = i === 0 ? apiGet('fixtures/events', { fixture: fid }, { ttl: 1800, timeoutMs: 10000 }) : null;
      const st = i < N_PARTITE_STATS_AVANZATE ? apiGet('fixtures/statistics', { fixture: fid }, { ttl: 1800, timeoutMs: 10000 }) : null;
      return Promise.all([ev, st]);
    });
    const esiti = await Promise.all(richieste);

    matches.forEach((m, i) => {
      const isHome = String(m.teams.home.id) === String(teamId);
      const gf = isHome ? m.goals.home : m.goals.away;
      const gs = isHome ? m.goals.away : m.goals.home;
      if (gf !== null && gf !== undefined && gs !== null && gs !== undefined) {
        totGf += toInt(gf); totGs += toInt(gs); mvGoals++;
        if (isHome) { gfHome += toInt(gf); gsHome += toInt(gs); nHome++; }
        else { gfAway += toInt(gf); gsAway += toInt(gs); nAway++; }
      }
      const [ev, sr] = esiti[i];
      if (ev) {
        for (const e of ev.response ?? []) {
          if (String(e.team.id) === String(teamId) && e.type === 'Card' && (e.detail ?? '').includes('Red')) sqCerti++;
        }
      }
      if (sr) {
        for (const ts of sr.response ?? []) {
          if (String(ts.team.id) === String(teamId)) {
            const s = {};
            for (const x of ts.statistics) s[x.type] = x.value;
            const poss = String(s['Ball Possession'] ?? '50%').replace('%', '');
            totPoss += /^\d+$/.test(poss) ? parseInt(poss, 10) : 50;
            totTiri += toInt(s['Shots on Goal']);
            totArea += toInt(s['Shots insidebox']);
            totCorn += toInt(s['Corner Kicks']);
            totFalli += toInt(s['Fouls']);
            totPar += toInt(s['Goalkeeper Saves']);
            totCart += toInt(s['Yellow Cards']) + toInt(s['Red Cards']);
            totRigori += toInt(s['Penalty Goals']);
            mvStats++;
          }
        }
      }
    });

    if (mvStats === 0) mvStats = 1;
    if (mvGoals === 0) mvGoals = 1;
    const avgPoss = totPoss / mvStats, avgTiri = totTiri / mvStats, avgArea = totArea / mvStats;
    const avgCorn = totCorn / mvStats, avgCart = totCart / mvStats, avgFalli = totFalli / mvStats;
    const avgPar = totPar / mvStats, avgGf = totGf / mvGoals, avgGs = totGs / mvGoals;
    const avgRig = totRigori / mvGoals;
    const golDaGioco = Math.max(0.1, avgGf - avgRig);
    const tiriDaGioco = Math.max(0.1, avgTiri - avgRig);
    let conv = golDaGioco > 0 ? tiriDaGioco / golDaGioco : 10.0;
    conv = Math.max(2.0, conv);
    let stile;
    if (avgPoss > 55 && avgArea < 4) stile = 'Tiki-Taka Sterile';
    else if (avgPoss < 45 && avgArea > 4) stile = 'Verticale Diretto';
    else stile = 'Bilanciato';
    return {
      poss: avgPoss, tiri: avgTiri, box: avgArea, conv, corn: avgCorn, cart: avgCart, falli: avgFalli,
      par: avgPar, stile, sqCerti, gf10: avgGf, gs10: avgGs, rig: avgRig,
      gfHome: gfHome / Math.max(1, nHome), gsHome: gsHome / Math.max(1, nHome),
      gfAway: gfAway / Math.max(1, nAway), gsAway: gsAway / Math.max(1, nAway), ok: true,
    };
  } catch (e) { return fallback; }
}

export async function analizzaSquadraGlobale(teamId) {
  const fallback = { mStanchezza: 1.0, isStanca: false, forma: 'N/D', mForma: 1.0, ritardi: [], punti5: 0, puntiPrev5: 0, ok: false };
  try {
    const r = await apiGet('fixtures', { team: teamId, last: 10, status: 'FT' }, { ttl: 3600, timeoutMs: 12000 });
    const matches = r.response ?? [];
    if (!matches.length) return { mStanchezza: 1.0, isStanca: false, forma: 'N/D', mForma: 1.0, ritardi: [], punti5: 0, puntiPrev5: 0, ok: true };

    const diffGiorni = giorniDa(parseData(matches[0].fixture.date));
    const isStanca = diffGiorni <= 4;
    const mStanchezza = isStanca ? 0.95 : 1.0;

    let forma = ''; let punti5 = 0; let puntiPrev5 = 0;
    matches.slice(0, 10).forEach((m, i) => {
      const isHome = String(m.teams.home.id) === String(teamId);
      const gh = m.goals.home; const ga = m.goals.away;
      if (gh === null || gh === undefined) return;
      let pt, ch;
      if (gh === ga) { pt = 1; ch = 'D'; }
      else if ((isHome && gh > ga) || (!isHome && ga > gh)) { pt = 3; ch = 'W'; }
      else { pt = 0; ch = 'L'; }
      if (i < 5) { forma += ch; punti5 += pt; } else puntiPrev5 += pt;
    });
    forma = forma.split('').reverse().join('');
    const mForma = 0.9 + (punti5 / 15) * 0.2;

    const consec = { W: 0, X: 0, L: 0, Over: 0, Goal: 0 };
    for (const m of matches) {
      const isHome = String(m.teams.home.id) === String(teamId);
      const gh = m.goals.home; const ga = m.goals.away;
      if (gh === null || gh === undefined || ga === null || ga === undefined) continue;
      if (gh === ga) { consec.X = 0; consec.W++; consec.L++; }
      else if ((isHome && gh > ga) || (!isHome && ga > gh)) { consec.W = 0; consec.X++; consec.L++; }
      else { consec.L = 0; consec.W++; consec.X++; }
      if ((gh + ga) > 2) consec.Over = 0; else consec.Over++;
      if (gh > 0 && ga > 0) consec.Goal = 0; else consec.Goal++;
    }
    const labelMap = { W: 'Vittoria', X: 'Pareggio', L: 'Sconfitta', Over: 'Over 2.5', Goal: 'Goal' };
    const ritardi = [];
    for (const [evento, n] of Object.entries(consec)) {
      const media = FREQUENZE_MEDIE[evento];
      if (n >= media) {
        const peso = n / media;
        const livello = peso >= 2.5 ? '🔴' : (peso >= 1.5 ? '🟠' : '🟡');
        ritardi.push({ evento, partite: n, peso, livello, label: `${livello} ${labelMap[evento]}: ${n}p (${peso.toFixed(1)}x media)` });
      }
    }
    return { mStanchezza, isStanca, forma, mForma, ritardi, punti5, puntiPrev5, ok: true };
  } catch (e) { return fallback; }
}

export async function analizzaH2hDnaEAndata(idCasa, idTrasf) {
  const fallback = { mH2hC: 1.0, mH2hT: 1.0, golC: 0, golT: 0, storico: 'Dati N/D', boostC: 1.0, boostT: 1.0, andataMsg: '', dettagli: 'Nessun dato.', ok: false };
  try {
    const r = await apiGet('fixtures/headtohead', { h2h: `${idCasa}-${idTrasf}`, last: 5 }, { ttl: 3600, timeoutMs: 10000 });
    const matches = r.response ?? [];
    if (!matches.length) return { mH2hC: 1.0, mH2hT: 1.0, golC: 0, golT: 0, storico: 'Nessun Precedente', boostC: 1.0, boostT: 1.0, andataMsg: '', dettagli: 'Nessun match.', ok: true };
    let vittC = 0, vittT = 0, golC = 0, golT = 0;
    let andataMsg = ''; let boostC = 1.0; let boostT = 1.0;
    const dettagli = [];
    for (const m of matches) {
      if (m.goals.home !== null && m.goals.home !== undefined) {
        const d = parseData(m.fixture.date);
        const dm = `${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()}`;
        dettagli.push(`📅 ${dm}: ${m.teams.home.name} <b>${m.goals.home} - ${m.goals.away}</b> ${m.teams.away.name}`);
      }
    }
    const detStr = dettagli.length ? dettagli.join('<br>') : 'Nessun dato.';
    const ult = matches[0];
    if (giorniDa(parseData(ult.fixture.date)) <= 28) {
      const ih = ult.teams.home.id === idCasa;
      const gcL = ult.goals.home; const gtL = ult.goals.away;
      if (gcL !== null && gcL !== undefined && gtL !== null && gtL !== undefined) {
        const gC = ih ? gcL : gtL; const gT = ih ? gtL : gcL;
        const diff = gC - gT;
        andataMsg = `🏆 Andata: ${gC} - ${gT}`;
        if (diff === -1 || diff === -2) { boostC = 1.25; andataMsg += " (Casa all'assalto ⚔️)"; }
        else if (diff === 1 || diff === 2) { boostT = 1.25; andataMsg += " (Ospiti all'assalto ⚔️)"; }
        else if (Math.abs(diff) >= 3) { boostC = boostT = 0.85; andataMsg += ' (Qualificazione chiusa 🛡️)'; }
      }
    }
    for (const m of matches) {
      if (m.goals.home === null || m.goals.home === undefined) continue;
      const ih = m.teams.home.id === idCasa;
      const gc = ih ? m.goals.home : m.goals.away;
      const gt = ih ? m.goals.away : m.goals.home;
      golC += gc; golT += gt;
      if (gc > gt) vittC++; else if (gt > gc) vittT++;
    }
    const cnt = Math.max(1, matches.filter(m => m.goals.home !== null && m.goals.home !== undefined).length);
    const tot = Math.max(1, golC + golT);
    const mC = Math.min(1.20, Math.max(0.80, 0.90 + (vittC / cnt) * 0.20 + (golC / (cnt * tot)) * 0.10));
    const mT = Math.min(1.20, Math.max(0.80, 0.90 + (vittT / cnt) * 0.20 + (golT / (cnt * tot)) * 0.10));
    const storico = `Vittorie: 🏠 ${vittC} - ${vittT} ✈️ | Gol H2H: ${golC} a ${golT}`;
    return { mH2hC: mC, mH2hT: mT, golC, golT, storico, boostC, boostT, andataMsg, dettagli: detStr, ok: true };
  } catch (e) { return fallback; }
}

export async function trovaLegaSquadra(teamId, season, fallbackId) {
  try {
    const r = await apiGet('leagues', { team: teamId, season }, { ttl: 86400, timeoutMs: 8000 });
    for (const e of r.response ?? []) if (e.league?.type === 'League') return e.league.id;
  } catch (e) { /* fallback */ }
  return fallbackId;
}

export async function rilevaContestoSpareggio(fixId, cId, tId, leagueIdC, leagueIdT, matchDateStr) {
  const result = {
    isInterlega: leagueIdC !== leagueIdT, isRitorno: false, aggregatoC: 0, aggregatoT: 0,
    boostC: 1.0, boostT: 1.0, msg: '', pesoMomentum: 0.80,
  };
  try {
    const h2h = await apiGet('fixtures/headtohead', { h2h: `${cId}-${tId}`, last: 4 }, { ttl: 3600, timeoutMs: 10000 });
    for (const m of h2h.response ?? []) {
      if (String(m.fixture.id) === String(fixId)) continue;
      const giorniFa = Math.round((parseData(matchDateStr) - parseData(m.fixture.date)) / 86400000);
      if (giorniFa >= 3 && giorniFa <= 21) {
        result.isRitorno = true;
        const ih = m.teams.home.id === cId;
        const gc = ih ? m.goals.home : m.goals.away;
        const gt = ih ? m.goals.away : m.goals.home;
        if (gc !== null && gc !== undefined && gt !== null && gt !== undefined) {
          result.aggregatoC = gc; result.aggregatoT = gt;
          const diff = gc - gt;
          if (diff > 0) { result.boostT = 1.30; result.boostC = 0.90; result.msg = `🔄 RITORNO | Aggregato: ${gc}-${gt} (Ospiti all'assalto)`; }
          else if (diff < 0) { result.boostC = 1.30; result.boostT = 0.90; result.msg = `🔄 RITORNO | Aggregato: ${gc}-${gt} (Casa all'assalto)`; }
          else { result.boostC = 1.20; result.boostT = 1.20; result.msg = `🔄 RITORNO | Aggregato: ${gc}-${gt} (Tutto aperto ⚖️)`; }
        }
        break;
      }
    }
  } catch (e) { /* ignora */ }
  if (result.isInterlega) {
    result.msg = (result.msg + ' ⚡ SPAREGGIO INTER-LEGA').trim();
    result.pesoMomentum = 1.0;
  }
  return result;
}

export async function scaricaMeteo(citta) {
  try {
    const r = await apiGet('meteo', { citta }, { ttl: 3600, timeoutMs: 5000 });
    const cond = r.current_condition[0].weatherDesc[0].value;
    const pioggia = ['rain', 'snow', 'shower', 'thunder'].some(p => cond.toLowerCase().includes(p));
    return pioggia ? [0.90, `🌧️ ${cond}`] : [1.0, `☀️ ${cond}`];
  } catch (e) { return [1.0, '🌥️ Dato N/D']; }
}

export async function scaricaRisultatoPartita(fixtureId) {
  const STATI_FINALI = new Set(['FT', 'AET', 'PEN']);
  try {
    const r = await apiGet('fixtures', { id: fixtureId }, { ttl: 0, timeoutMs: 12000 });
    if (!r.response?.length) return null;
    const f = r.response[0];
    const stato = f.fixture.status.short;
    const ft = f.score.fulltime; const ht = f.score.halftime;
    if (ft.home === null || ft.home === undefined || ft.away === null || ft.away === undefined) {
      return { finita: false, gcFt: null, gtFt: null, gcHt: null, gtHt: null };
    }
    return { finita: STATI_FINALI.has(stato), gcFt: ft.home, gtFt: ft.away, gcHt: ht?.home ?? null, gtHt: ht?.away ?? null };
  } catch (e) { return null; }
}
