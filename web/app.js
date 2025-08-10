/* Aurora UI — staggered polling + local time tables */

const $ = q => document.querySelector(q);
const setJSON = (sel, val) => { $(sel).textContent = typeof val === 'string' ? val : JSON.stringify(val, null, 2); };
const statusEl = () => $('#status');
const toLocal = (s) => {
  try { const d = new Date(s); return isNaN(d) ? s : d.toLocaleString(undefined,{hour12:false}); }
  catch { return s; }
};

async function api(path, opt = {}) {
  const r = await fetch(path, { credentials: 'include', ...opt });
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
}

/* ------ Render helpers ------ */
function renderTrades(rows) {
  const head = $('#trades thead'), body = $('#trades tbody');
  if (!head || !body) return;
  if (!rows || !rows.length) {
    head.innerHTML = '<tr><th>ts</th><th>symbol</th><th>plugin</th><th>side</th><th>price</th><th>qty</th><th>cash_delta</th><th>balance_after</th><th>pos_qty_after</th><th>avg_price_after</th></tr>';
    body.innerHTML = '<tr><td colspan="10" class="muted">No trades yet</td></tr>'; return;
  }
  const cols = ['ts','symbol','plugin','side','price','qty','cash_delta','balance_after','pos_qty_after','avg_price_after'];
  head.innerHTML = '<tr>' + cols.map(c => `<th>${c}</th>`).join('') + '</tr>';
  body.innerHTML = rows.map(r => '<tr>' + cols.map(c => {
    let v = r[c];
    if (c === 'ts') v = toLocal(v);
    return `<td>${v}</td>`;
  }).join('') + '</tr>').join('');
}

function renderPositionsTable(obj) {
  const head = $('#positionsTbl thead'), body = $('#positionsTbl tbody');
  if (!head || !body) return;
  // obj looks like: { balance: ..., positions: { "BTCUSDT": { qty, avg_price }, ... }, realized_pnl, unrealized_pnl }
  const rows = [];
  if (obj && obj.positions) {
    for (const [symbol, p] of Object.entries(obj.positions)) {
      rows.push({ symbol, qty: p.qty, avg_price: p.avg_price });
    }
  }
  head.innerHTML = '<tr><th>symbol</th><th>qty</th><th>avg_price</th></tr>';
  if (!rows.length) { body.innerHTML = '<tr><td colspan="3" class="muted">No open positions</td></tr>'; return; }
  body.innerHTML = rows.map(r => `<tr><td>${r.symbol}</td><td>${r.qty}</td><td>${r.avg_price}</td></tr>`).join('');
}

/* ------ One-per-panel loaders ------ */
async function loadHealth()    { const d = await api('/health');      setJSON('#health', d); }
async function loadPositions() { const d = await api('/positions');   setJSON('#positions', d); renderPositionsTable(d); }
async function loadAIStatus()  { const d = await api('/ai/status');   setJSON('#ai', d); }
async function loadTickAuto()  { const d = await api('/tick/auto');   setJSON('#tickcfg', d); }
async function loadRisk()      { const d = await api('/risk');        setJSON('#risk', d); }
async function loadTrades()    { const d = await api('/logs/trades?n=200'); renderTrades(d.trades || []); }

/* ------ Controls ------ */
async function startLoop(){ const v=parseFloat($('#interval').value||'0.5'); await api(`/tick/auto?enabled=true&interval=${v}`, {method:'POST'}); await loadTickAuto(); }
async function stopLoop(){ await api(`/tick/auto?enabled=false`, {method:'POST'}); await loadTickAuto(); }
async function tickOnce(){ await api('/tick'); await Promise.all([loadHealth(), loadPositions()]); }

async function setEps(){ const v=parseFloat($('#eps').value||'0.1'); await api(`/ai/eps?eps=${v}`, {method:'POST'}); await loadAIStatus(); }
async function setStake(){ const v=parseFloat($('#stake').value||'0.1'); await api(`/ai/stake?stake=${v}`, {method:'POST'}); await loadAIStatus(); }

async function orderPreview(){ const side=$('#side').value, f=parseFloat($('#fraction').value||'0.1'); setJSON('#orderOut', await api(`/orders/preview?side=${encodeURIComponent(side)}&fraction=${f}`)); }
async function orderSubmit(){ const side=$('#side').value, f=parseFloat($('#fraction').value||'0.1'); setJSON('#orderOut', await api(`/orders?side=${encodeURIComponent(side)}&fraction=${f}&plugin=dashboard`, {method:'POST'})); await Promise.all([loadHealth(), loadPositions(), loadTrades()]); }

async function applyRisk(){ const stakeCap=parseFloat($('#risk_stake_cap').value||'10'); setJSON('#risk', await api(`/risk?stake_cap_pct=${stakeCap}`, {method:'POST'})); }

/* ------ Wire buttons ------ */
window.addEventListener('DOMContentLoaded', () => {
  $('#btnStart').onclick = startLoop;
  $('#btnStop').onclick = stopLoop;
  $('#btnTick').onclick = tickOnce;
  $('#btnEps').onclick = setEps;
  $('#btnStake').onclick = setStake;
  $('#btnPreview').onclick = orderPreview;
  $('#btnSubmit').onclick = orderSubmit;
  $('#btnRisk').onclick = applyRisk;
});

/* ------ Staggered polling engine ------ */
const tasks = [
  { name:'health',    fn: wrap(loadHealth,    '#health'),    offset:   0 },
  { name:'positions', fn: wrap(loadPositions, '#positions'), offset: 500 },
  { name:'ai',        fn: wrap(loadAIStatus,  '#ai'),        offset:1000 },
  { name:'tick',      fn: wrap(loadTickAuto,  '#tickcfg'),   offset:1500 },
  { name:'risk',      fn: wrap(loadRisk,      '#risk'),      offset:2000 },
  { name:'trades',    fn: wrap(loadTrades,    '#trades'),    offset:2500 }
];

function wrap(fn, panelSel){
  let running = false;
  return async () => {
    if (running) return;
    running = true;
    try { await fn(); updateStatus(); }
    catch (e) {
      if (panelSel === '#trades') renderTrades([]);
      setJSON(panelSel, String(e.message || e)); updateStatus();
    }
    finally { running = false; }
  };
}

function updateStatus(){ statusEl().textContent = 'OK'; }

function startPolling(){
  const period = 6000; // each panel refreshes every 6s
  tasks.forEach(t => { setTimeout(t.fn, t.offset); setInterval(t.fn, period); });
}
startPolling();
