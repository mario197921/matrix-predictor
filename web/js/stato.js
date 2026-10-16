// stato.js — stato condiviso dell'app (equivalente di st.session_state) e utilità UI.
export const BUDGET_INIZIALE = 10.0;   // soldi con cui si è iniziato a giocare

export const S = {
  user: null,
  storico: [],
  dataMaster: new Map(),   // campionato -> partite
  allTips: [],
  carrello: new Map(),     // `${Match}_${Tip}` -> selezione
  activeLeagues: null,
  budgetTotale: 50,
  start: '', end: '',
  aperti: new Set(),       // id dei <details> aperti (sopravvivono ai re-render)
  tabAttivo: 't1',
};

export const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
// consente solo <b> e <br> (usati nei dettagli H2H generati dal codice)
export const htmlSicuro = s => esc(s).replace(/&lt;(\/?)b&gt;/g, '<$1b>').replace(/&lt;br&gt;/g, '<br>');
export const fmt = (x, n = 2) => Number(x ?? 0).toFixed(n);
export const sgn = (x, n = 1) => `${x >= 0 ? '+' : ''}${Number(x).toFixed(n)}`;
export const $ = (sel, root = document) => root.querySelector(sel);
export const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
export const oggiStr = () => {
  const d = new Date(); const p = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
};

export function metrica(label, valore, dettaglio = '') {
  return `<div class="metric"><div class="metric-l">${esc(label)}</div><div class="metric-v">${valore}</div>${dettaglio ? `<div class="metric-d">${dettaglio}</div>` : ''}</div>`;
}

// <details> con stato ricordato
export function dettagli(id, titolo, corpo, { aperto = false, classe = 'exp' } = {}) {
  const open = S.aperti.has(id) || aperto;
  return `<details class="${classe}" data-id="${esc(id)}"${open ? ' open' : ''}><summary>${titolo}</summary><div class="exp-body">${corpo}</div></details>`;
}
document.addEventListener('toggle', e => {
  const d = e.target;
  if (d.tagName === 'DETAILS' && d.dataset.id) { if (d.open) S.aperti.add(d.dataset.id); else S.aperti.delete(d.dataset.id); }
}, true);

export function avviso(testo, tipo = 'warn') {
  const box = document.getElementById('avvisi');
  const el = document.createElement('div');
  el.className = `alert alert-${tipo}`;
  el.textContent = testo;
  box.appendChild(el);
  if (tipo !== 'err') setTimeout(() => el.remove(), 12000);
  return el;
}

export function scaricaFile(nome, contenuto, mime = 'text/plain') {
  const blob = new Blob([contenuto], { type: `${mime};charset=utf-8` });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = nome; document.body.appendChild(a); a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 500);
}
export const timestampFile = () => {
  const d = new Date(); const p = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}_${p(d.getHours())}${p(d.getMinutes())}`;
};
