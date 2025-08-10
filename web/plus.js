// ---- Aurora UI+ extras ----

// helper
function $(sel){ return document.querySelector(sel); }

// Inject "Signal" card
function injectSignalCard(){
  const grid = document.querySelector('.grid') || document.body;
  if (document.getElementById('signal_card')) return;
  const wrap = document.createElement('div');
  wrap.className = 'card';
  wrap.id = 'signal_card';
  wrap.innerHTML = `
    <div class="card-title">Signal</div>
    <div id="signal_box" class="mono small">
      <div id="signal_text">Loading…</div>
      <div class="bar"><div id="signal_bar" class="bar-fill" style="width:0%"></div></div>
    </div>`;
  // Try to place it nicely as the first card; fallback append
  const firstCard = document.querySelector('.grid .card');
  if (firstCard && firstCard.parentNode) {
    firstCard.parentNode.insertBefore(wrap, firstCard.nextSibling);
  } else {
    grid.appendChild(wrap);
  }
}

// Fetch & render readiness
async function loadReadiness(){
  try{
    const r = await fetch('/ai/readiness');
    if(!r.ok) throw new Error(r.statusText);
    const d = await r.json();
    const t = document.getElementById('signal_text');
    const b = document.getElementById('signal_bar');
    if (t) t.textContent = `${d.awaiting ? 'Awaiting entry' : 'Signal active'} · action=${d.action} · readiness=${d.readiness}%`;
    if (b) b.style.width = `${d.readiness}%`;
  }catch(e){
    const t = document.getElementById('signal_text');
    if (t) t.textContent = 'Signal unavailable';
  }
}

// Override renderTrades to (a) cap at 50, (b) localize time, (c) keep columns
(function overrideRenderTrades(){
  const original = window.renderTrades;
  window.renderTrades = function(rows){
    const head = document.querySelector('#trades thead');
    const body = document.querySelector('#trades tbody');
    if (!head || !body){ if(original) return original(rows); else return; }
    if (!rows || !rows.length){
      head.innerHTML = '';
      body.innerHTML = '<tr><td>No trades yet</td></tr>';
      return;
    }
    const cols = Object.keys(rows[0]);
    head.innerHTML = '<tr>' + cols.map(c => `<td>${c}</td>`).join('') + '</tr>';
    const lim = rows.slice(0, 50).map(r => {
      const k = ('ts' in r) ? 'ts' : (('time' in r) ? 'time' : (('date' in r) ? 'date' : null));
      if (k){
        try{
          const dt = new Date(r[k]);
          r[k] = dt.toLocaleString(undefined, {
            year:'numeric', month:'2-digit', day:'2-digit',
            hour:'2-digit', minute:'2-digit', second:'2-digit'
          });
        }catch(_){}
      }
      return r;
    });
    body.innerHTML = lim.map(r => '<tr>' + cols.map(c => `<td>${r[c]}</td>`).join('') + '</tr>').join('');
  };
})();

// Boot
window.addEventListener('DOMContentLoaded', () => {
  injectSignalCard();
  loadReadiness().catch(()=>{});
  setInterval(() => loadReadiness().catch(()=>{}), 7000);
});
