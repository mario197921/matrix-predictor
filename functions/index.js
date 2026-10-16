// Proxy verso API-Football (api-sports.io) per Matrix Bet.
// - La chiave API vive solo qui (secret API_KEY_FOOTBALL), mai nel browser.
// - Accetta solo richieste con un ID token Firebase valido del proprietario.
// - Inoltra solo endpoint in whitelist e mette in cache le risposte in memoria.
const { onRequest } = require('firebase-functions/v2/https');
const { defineSecret } = require('firebase-functions/params');
const admin = require('firebase-admin');

admin.initializeApp();
const API_KEY = defineSecret('API_KEY_FOOTBALL');
const EMAIL_AUTORIZZATA = 'mariodt79@gmail.com';

const ENDPOINT_OK = new Set([
  'leagues', 'fixtures', 'fixtures/events', 'fixtures/statistics', 'fixtures/headtohead',
  'standings', 'odds', 'injuries', 'players', 'teams/statistics',
]);
const TTL_MAX = 7 * 24 * 3600;
const cache = new Map(); // chiave -> { scade, corpo }
const CACHE_MAX = 3000;

async function utenteAutorizzato(req) {
  const h = req.get('authorization') || '';
  const m = h.match(/^Bearer (.+)$/);
  if (!m) return false;
  try {
    const t = await admin.auth().verifyIdToken(m[1]);
    return t.email === EMAIL_AUTORIZZATA && t.email_verified === true;
  } catch (e) { return false; }
}

async function conTimeout(url, opts, ms) {
  const ac = new AbortController();
  const id = setTimeout(() => ac.abort(), ms);
  try { return await fetch(url, { ...opts, signal: ac.signal }); }
  finally { clearTimeout(id); }
}

exports.api = onRequest(
  { region: 'europe-west1', secrets: [API_KEY], timeoutSeconds: 60, memory: '256MiB', maxInstances: 5, cors: false },
  async (req, res) => {
    res.set('Cache-Control', 'no-store');
    if (req.method !== 'GET') return res.status(405).json({ errore: 'metodo non consentito' });
    if (!(await utenteAutorizzato(req))) return res.status(401).json({ errore: 'non autorizzato' });

    // /api/<endpoint...>?params&ttl=secondi
    const path = req.path.replace(/^\/+api\/+/, '').replace(/^\/+|\/+$/g, '');
    const q = { ...req.query };
    const ttl = Math.max(0, Math.min(TTL_MAX, parseInt(q.ttl || '0', 10) || 0));
    delete q.ttl;

    try {
      if (path === 'meteo') {
        const citta = String(q.citta || '').slice(0, 80);
        if (!citta) return res.status(400).json({ errore: 'citta mancante' });
        const r = await conTimeout(`https://wttr.in/${encodeURIComponent(citta)}?format=j1`, {}, 3000);
        return res.status(r.status).type('application/json').send(await r.text());
      }
      if (!ENDPOINT_OK.has(path)) return res.status(404).json({ errore: 'endpoint non consentito' });

      const qs = new URLSearchParams(Object.entries(q).map(([k, v]) => [k, String(v)]));
      qs.sort();
      const chiave = `${path}?${qs.toString()}`;
      const ora = Date.now();
      const hit = cache.get(chiave);
      if (ttl > 0 && hit && hit.scade > ora) return res.status(200).type('application/json').send(hit.corpo);

      const r = await conTimeout(`https://v3.football.api-sports.io/${path}?${qs.toString()}`,
        { headers: { 'x-apisports-key': API_KEY.value() } }, 20000);
      const corpo = await r.text();
      if (r.ok && ttl > 0) {
        if (cache.size >= CACHE_MAX) cache.delete(cache.keys().next().value);
        cache.set(chiave, { scade: ora + ttl * 1000, corpo });
      }
      return res.status(r.status).type('application/json').send(corpo);
    } catch (e) {
      return res.status(502).json({ errore: 'errore upstream', dettaglio: String(e && e.message || e) });
    }
  }
);
