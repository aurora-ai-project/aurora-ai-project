/* Aurora UI — staggered polling (no Nginx bursts) */

const $ = q => document.querySelector(q);
const setJSON = (sel, val) => { $(sel).textContent = typeof val === 'string' ? val : JSON.stringify(val, null, 2); };
const statusEl = () => $('#status');

async function api(path, opt = {}) {
  const r = await fetch(path, { credentials: 'include', ...opt });
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
}

/* ------ Render helpers ------ */
function renderTrades(rows) {
  const toLocal=(s)=>{try{const d=new Date(s);return isNaN(d)?s:d.toLocaleString(undefined,{hour12:false});}catch(e){return s}}
  const head = $('#trades thead'), body = $('#trades tbody');
  if (!head || !body) return;
  if (!rows || !rows.length) { head.innerHTML = ''; body.innerHTML = '<tr><td>No trades yet</td></tr>'; return; }
  const cols = Object.keys(rows[0]);
  head.innerHTML = '<tr>' + cols.map(c => `<td>${c}</td>`).join('') + '</tr>';
  body.innerHTML = rows.map(r => '<tr>' + cols.map(c => `<td>${r[c]}</td>`).join('') + '</tr>').join('');
}

/* ------ One-per-panel loaders ------ */
async function loadHealth()    { const d = await api('/health');      setJSON('#health', d); }
async function loadPositions() { const d = await api('/positions');   setJSON('#positions', d); }
async function loadAIStatus()  { const d = await api('/ai/status');   setJSON('#ai', d); }
async function loadTickAuto()  { const d = await api('/tick/auto');   setJSON('#tickcfg', d); }
async function loadRisk()      { const d = await api('/risk');        setJSON('#risk', d); }
async function loadTrades()    { const d = await api('/logs/trades?n=25'); renderTrades(d.trades || []); }

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
/* Each fn fires every 6s, offset so only one request is active at a time */
const tasks = [
  { name:'health',    fn: wrap(loadHealth,    '#health'),    offset:   0 },
  { name:'positions', fn: wrap(loadPositions, '#positions'), offset: 500 },
  { name:'ai',        fn: wrap(loadAIStatus,  '#ai'),        offset:1000 },
  { name:'tick',      fn: wrap(loadTickAuto,  '#tickcfg'),   offset:1500 },
  { name:'risk',      fn: wrap(loadRisk,      '#risk'),      offset:2000 },
  { name:'trades',    fn: wrap(loadTrades,    '#trades'),    offset:2500 }
];

function wrap(fn, panelSel){
  let running = false, fails = 0;
  return async () => {
    if (running) return; // single-flight guard
    running = true;
    try {
      await fn();
      fails = 0;
      updateStatus();
    } catch (e) {
      fails = Math.min(fails + 1, 6);
      // Show per-panel error without killing others
      if (panelSel === '#trades') renderTrades([]);
      setJSON(panelSel, String(e.message || e));
      updateStatus();
    } finally {
      running = false;
    }
  };
}

function updateStatus(){
  // Count visible errors in panels
  const err = [...document.querySelectorAll('pre')]
    .map(p => p.textContent.startsWith('Error') || /^\d{3}\s/.test(p.textContent))
    .filter(Boolean).length;
  statusEl().textContent = err ? `OK (some panels retrying…)` : 'OK';
}

function startPolling(){
  const period = 8000; // each panel refreshes every 6s
  tasks.forEach(t => {
    setTimeout(t.fn, t.offset);           // initial stagger
    setInterval(t.fn, period);            // steady cadence
  });
}
startPolling();
