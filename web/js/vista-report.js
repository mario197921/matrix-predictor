// vista-report.js — pagina nascosta ?vista=report_analitico_interno: report
// aggregato + simulazione del bankroll virtuale, con JSON scaricabile.
import { S, BUDGET_INIZIALE, esc, fmt, metrica, scaricaFile, oggiStr, $ } from './stato.js';
import { leggiStorico } from './db.js';
import { costruisciReportAnalitico } from './report.js';

function graficoLinea(valori) {
  if (!valori.length) return '';
  const W = 800, H = 220, P = 24;
  const min = Math.min(0, ...valori), max = Math.max(0, ...valori);
  const span = (max - min) || 1;
  const x = i => P + (valori.length === 1 ? 0 : (i / (valori.length - 1)) * (W - 2 * P));
  const y = v => H - P - ((v - min) / span) * (H - 2 * P);
  const punti = valori.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(' ');
  return `<svg class="svg-chart" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">
    <line x1="${P}" x2="${W - P}" y1="${y(0)}" y2="${y(0)}" stroke="#3a4560" stroke-dasharray="4 4"/>
    <polyline fill="none" stroke="#4f8ef7" stroke-width="2" points="${punti}"/>
    <text x="${P}" y="14" fill="#8b95b0" font-size="11">max ${max.toFixed(2)}€</text>
    <text x="${P}" y="${H - 6}" fill="#8b95b0" font-size="11">min ${min.toFixed(2)}€</text></svg>`;
}

export async function renderReport() {
  const box = $('#vista-report');
  box.innerHTML = '<h1>📊 Report analitico interno</h1><div class="alert">Lettura dello storico da Firebase…</div>';
  let storico = [];
  try { storico = await leggiStorico(365); }
  catch (e) { box.innerHTML = `<h1>📊 Report analitico interno</h1><div class="alert alert-err">Errore Firebase: ${esc(e.message)}</div>`; return; }
  if (!storico.length) { box.innerHTML = '<h1>📊 Report analitico interno</h1><div class="alert alert-warn">Nessuna schedina trovata su Firebase.</div>'; return; }

  const report = costruisciReportAnalitico(storico, BUDGET_INIZIALE);
  const json = JSON.stringify(report, null, 2);
  const sim = report.simulazione_virtuale; const bl = sim.bankroll_limitato;
  const righe = Object.entries(sim.per_gruppo).map(([k, v]) => `<tr><td>${esc(k)}</td><td class="num">${v.concluse}</td><td class="num">${v.vinte}</td>
    <td class="num">${v['win_rate_%']}%</td><td class="num">${fmt(v.puntato)}</td><td class="num">${fmt(v.pl)}</td><td class="num">${v['roi_%']}%</td></tr>`).join('');
  box.innerHTML = `<h1>📊 Report analitico interno</h1>
    <div class="muted small">Pagina non collegata al resto dell'app: usala solo per scaricare i dati aggregati da passare per l'analisi della strategia.</div>
    <div class="alert alert-ok">Report generato su ${report.n_schedine_totali} schedine.</div>
    <p><b>Simulazione virtuale</b> — ${fmt(sim.puntata)}€ fissi su ognuna delle ${sim.n_schedine_concluse} schedine concluse, dalla prima in memoria</p>
    <div class="cols cols-4">
      ${metrica('P&L totale', `${sim.pl_totale >= 0 ? '+' : ''}${fmt(sim.pl_totale)}€`)}
      ${metrica('ROI', sim['roi_%'] !== null ? `${sim['roi_%'] >= 0 ? '+' : ''}${sim['roi_%']}%` : '—')}
      ${metrica('Max drawdown', fmt(sim.max_drawdown) + '€')}
      ${metrica(`Bankroll da ${Math.round(sim.bankroll_iniziale)}€`, fmt(bl.saldo_finale) + '€', bl.fermato_alla_schedina_n ? `finito alla schedina n.${bl.fermato_alla_schedina_n}` : 'mai finito')}
    </div>
    ${righe ? `<div class="tbl-wrap" style="margin-top:14px;"><table class="tbl"><thead><tr><th>gruppo</th><th>concluse</th><th>vinte</th><th>win rate</th><th>puntato</th><th>pl</th><th>roi</th></tr></thead><tbody>${righe}</tbody></table></div>` : ''}
    ${graficoLinea(sim.curva.map(c => c.pl_cumulato))}
    <div class="inline-ctl" style="margin-top:14px;"><button class="btn" id="btn-json">📥 Scarica report analitico (JSON)</button></div>
    <details class="exp"><summary>Mostra/copia JSON grezzo</summary><div class="exp-body"><textarea class="json" readonly>${esc(json)}</textarea></div></details>`;
  $('#btn-json').addEventListener('click', () => scaricaFile(`report_analitico_${oggiStr()}.json`, json, 'application/json'));
}
