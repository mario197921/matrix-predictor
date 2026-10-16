import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import * as M from '../web/js/modello.js';
import * as R from '../web/js/report.js';

const G = JSON.parse(readFileSync(new URL('./golden.json', import.meta.url)));
const EPS = 1e-9;

function vicini(a, b, path = '') {
  if (typeof a === 'number' && typeof b === 'number') {
    assert.ok(Math.abs(a - b) <= EPS * Math.max(1, Math.abs(a), Math.abs(b)), `${path}: ${a} != ${b}`);
  } else if (Array.isArray(a) && Array.isArray(b)) {
    assert.equal(a.length, b.length, `${path}: lunghezza`);
    a.forEach((x, i) => vicini(x, b[i], `${path}[${i}]`));
  } else if (a && b && typeof a === 'object' && typeof b === 'object') {
    assert.deepEqual(Object.keys(a).sort(), Object.keys(b).sort(), `${path}: chiavi`);
    for (const k of Object.keys(a)) vicini(a[k], b[k], `${path}.${k}`);
  } else assert.equal(a, b, path);
}

test('mercati: stessi valori e stesso ordine di Python', () => {
  for (const c of G.mercati) {
    const out = M.calcolaTuttiIMercati(...c.args);
    assert.deepEqual([...out.keys()], c.out.map(x => x[0]));
    vicini([...out.values()], c.out.map(x => x[1]));
  }
});

test('blend 1X2 sul mercato', () => {
  for (const c of G.blend) {
    const out = M.applicaBlendMercato1x2(new Map(c.full), c.q, c.peso);
    assert.deepEqual([...out.keys()], c.out.map(x => x[0]));
    vicini([...out.values()], c.out.map(x => x[1]));
  }
});

test('quota finale, edge, kelly', () => {
  for (const c of G.quota) {
    const [q, real] = M.getQuotaFinale(c.tip, c.prob, c.reali);
    assert.equal(q, c.q); assert.equal(real, c.real);
    vicini(M.calcolaEdgePct(c.prob, q), c.edge);
    vicini(M.kellyFraction(c.prob, q), c.kelly);
  }
});

test('costruzione schedine = Python (edge, prob, prob_range)', () => {
  for (const c of G.schedine) {
    const p = c.params;
    const opts = { ...p, escludiMatch: new Set(c.escludi) };
    delete opts.minQ; delete opts.maxQ; delete opts.target;
    const [sel, q, pr, usati] = M.costruisciSchedinaDinamica(c.pool, p.minQ, p.maxQ, p.target, opts);
    assert.deepEqual(sel.map(s => s.id), c.ids, JSON.stringify(p));
    vicini(q, c.q); vicini(pr, c.p);
    assert.deepEqual([...usati].sort(), c.usati);
  }
});

test('valutazione esiti dei mercati', () => {
  for (const c of G.esiti) {
    const out = M.valutaEsitoTip(c.tip, ...c.args);
    assert.equal(out, c.out, `${c.tip} ${c.args}`);
  }
});

test('utility: famiglie, nomi, prior', () => {
  for (const [t, f] of G.famiglie) assert.equal(M.getFamily(t), f, t);
  for (const [n, s] of G.nomi) assert.equal(M.semplificaNome(n), s, n);
  for (const [cur, prev, g, out] of G.prior) vicini(M.blendPriorStagione(cur, prev, g), out);
});

test('record schedina', () => {
  const rec = M.costruisciRecordSchedina('PROB_SAFETY', '2026-10-16', [
    { Match: 'A vs B', Tip: '1', Prob: 62.345, Quota: 1.456, Edge: 3.456, League: 'Serie A', FixtureID: 99 },
    { Match: 'C vs D', Tip: 'O2.5', Prob: 55.0, Quota: 1.8 }], 2.62, 0.343, 5.0, 'X', 'prob');
  assert.deepEqual(rec, G.record);
});

test('simulazione bankroll virtuale = Python', () => {
  vicini(R.simulaBankrollVirtuale(G.storico, 1.0, 10.0), G.sim);
  vicini(R.simulaBankrollVirtuale(G.storico, 2.5, 3.0), G.sim2);
});

test('report analitico = Python', () => {
  vicini(R.costruisciReportAnalitico(G.storico, 10.0), G.report);
  vicini(R.costruisciReportAnalitico(G.storico), G.report0);
});
