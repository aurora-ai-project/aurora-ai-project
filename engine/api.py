import asyncio, contextlib
from fastapi import FastAPI, Query, Depends
from .security import check
from contextlib import asynccontextmanager
from .state import load_state, save_state
from .loader import load_plugins, plugin_spec
from . import ticker
from .datafeed import FEED
from .logview import tail_trades
from . import risk
from .orders import preview as preview_order, submit as submit_order
from .ai_agent import set_eps, set_stake, save as ai_save, load as ai_load, status as ai_status

async def heartbeat_loop():
    while True:
        state = load_state()
        save_state(state)
        await asyncio.sleep(5)

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_plugins()
    hb = asyncio.create_task(heartbeat_loop())
    tk = ticker.start_background(asyncio.get_event_loop())
    try:
        yield
    finally:
        hb.cancel()
        with contextlib.suppress(Exception):
            await hb
        ticker.stop_background()
        with contextlib.suppress(Exception):
            await tk

app = FastAPI(title="AURORA AI Core", lifespan=lifespan, dependencies=[Depends(check)])

@app.get("/health")
def health():
    state = load_state()
    save_state(state)
    return {"status":"ok","state":state}

@app.get("/plugins")
def list_plugins():
    return {"plugins": load_state().get("plugins", [])}

@app.get("/plugin")
def list_plugins_alias():
    return list_plugins()

def _do_refresh():
    loaded = load_plugins()
    return {"ok": True, "loaded": loaded, "plugins": load_state().get("plugins", [])}

@app.get("/plugins/refresh")
@app.post("/plugins/refresh")
def refresh_plugins():
    return _do_refresh()

# --- Tick controls ---
@app.get("/tick")
async def tick_once():
    return await ticker.tick_once()

@app.get("/tick/auto")
def tick_auto_get():
    return {"config": ticker.get_config()}

@app.post("/tick/auto")
def tick_auto_post(enabled: bool | None = None, interval: float | None = None):
    return {"config": ticker.set_config(enabled=enabled, interval=interval)}

# --- Data / Spec ---
@app.get("/price")
def price():
    return FEED.next()

@app.get("/plugins/spec")
def spec():
    return plugin_spec()

# --- Positions / Logs ---
@app.get("/positions")
def positions():
    st = load_state()
    return {
        "balance": st.get("balance"),
        "positions": st.get("positions", {}),
        "unrealized_pnl": st.get("unrealized_pnl", 0.0),
        "realized_pnl": st.get("realized_pnl", 0.0)
    }

@app.get("/logs/trades")
def logs_trades(n: int = Query(50, ge=1, le=1000)):
    return {"trades": tail_trades(n)}

# --- Risk config ---
@app.get("/risk")
def get_risk():
    st = load_state()
    return risk.get_config(st)

@app.post("/risk")
def set_risk(
    max_drawdown_pct: float | None = None,
    stake_cap_pct: float | None = None,
    min_cash_reserve_pct: float | None = None,
    sl_pct: float | None = None,
    tp_pct: float | None = None,
    tp_partial_pct: float | None = None,
):
    st = load_state()
    cfg = risk.set_config(
        st,
        max_drawdown_pct=max_drawdown_pct,
        stake_cap_pct=stake_cap_pct,
        min_cash_reserve_pct=min_cash_reserve_pct,
        sl_pct=sl_pct,
        tp_pct=tp_pct,
        tp_partial_pct=tp_partial_pct,
    )
    save_state(st)
    return cfg

# --- Manual orders ---
@app.get("/orders/preview")
def orders_preview(
    side: str = Query(..., pattern="^(?i)(buy|sell|exit)$"),
    fraction: float = Query(0.10, ge=0.0, le=1.0),
    price: float | None = None,
):
    if price is None:
        # use latest feed price (advances once)
        price = FEED.next()["price"]
    return preview_order(side, fraction, price)

@app.post("/orders")
def orders_submit(
    side: str = Query(..., pattern="^(?i)(buy|sell|exit)$"),
    fraction: float = Query(0.10, ge=0.0, le=1.0),
    price: float | None = None,
    plugin: str = "manual",
):
    if price is None:
        price = FEED.next()["price"]
    return submit_order(side, fraction, price, plugin=plugin)


@app.get("/ai/status")
def ai_model_status():
    return ai_status()
# --- Aurora extra: readiness endpoint ---
@app.get("/ai/readiness", dependencies=[Depends(secure)])
def ai_readiness():
    """
    Show whether we're awaiting an entry and how 'ready' we are.
    Uses last AI 'conf' as [0..1] mapped to 0..100%.
    """
    st = load_state()
    ai = st.get("ai", {}) or {}
    last = ai.get("last", {}) or {}
    action = (last.get("action") or "HOLD").upper()
    conf = last.get("conf")
    try:
        conf = float(conf or 0.0)
    except Exception:
        conf = 0.0
    readiness = max(0.0, min(100.0, round(conf * 100.0, 2)))
    awaiting = action == "HOLD"
    reason = "confidence below threshold" if awaiting else "signal active"
    return {
        "awaiting": awaiting,
        "action": action,
        "readiness": readiness,
        "reason": reason,
    }
