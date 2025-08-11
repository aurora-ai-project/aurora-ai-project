import os, pathlib
from fastapi import FastAPI, Body, Query
from fastapi.staticfiles import StaticFiles
from engine.pricefeed import feed
from engine.plugins import load_plugins, reload_plugins, combine_votes
from .ticker import ticker
from .trading import account

app = FastAPI(title="Aurora Engine API")

_plugins = None
def _ensure_plugins():
    global _plugins
    if _plugins is None:
        _plugins = load_plugins()
        for lp in _plugins:
            feed.subscribe(lp.obj.on_price)
    return _plugins

@app.on_event("startup")
async def _startup():
    _ensure_plugins()
    if os.getenv("AURORA_AUTOSTART", "1") == "1":
        ticker.start()

@app.get("/health")
async def health():
    return {"ok": True}

@app.get("/status")
async def status():
    running = bool(ticker._task and not ticker._task.done())
    return {
        "running": running,
        "last_tick": ticker.last_tick,
        "count": getattr(ticker, "count", None),
        "prices": len(feed.buffer),
        "plugins": [p.name for p in _ensure_plugins()],
    }

@app.get("/plugins")
async def plugins():
    return {"loaded": [p.name for p in _ensure_plugins()]}

@app.post("/plugins/reload")
async def plugins_reload():
    feed._subscribers.clear()
    plugs = reload_plugins()
    for lp in plugs:
        feed.subscribe(lp.obj.on_price)
    return {"reloaded": [p.name for p in plugs]}

@app.post("/price/push")
async def price_push(price: float = Body(..., embed=True)):
    n = feed.push(price)
    return {"buffer": n, "last": price}

@app.post("/decide")
async def decide():
    plugs = _ensure_plugins()
    votes = [lp.obj.vote() for lp in plugs]
    combined = combine_votes(votes)
    return {"votes": dict((lp.name, lp.obj.vote()) for lp in plugs), "combined": combined}

@app.get("/account/status")
async def account_status():
    last = feed.last(1)
    price = last[-1] if last else 0.0
    return account.status(price)

@app.post("/trade/execute")
async def trade_execute(action: str = Body(..., embed=True)):
    last = feed.last(1)
    if not last:
        return {"error": "no price in buffer; push a price first"}
    price = float(last[-1])
    sltp = account.apply_sl_tp(price)
    act = action.lower()
    if sltp and act == "hold":
        act = sltp
    if act not in ("buy","sell","hold"):
        return {"error": "action must be buy/sell/hold"}
    return account.execute(act, price)

@app.post("/tick/once")
async def tick_once():
    return await ticker.tick_once()

@app.post("/tick/start")
async def tick_start():
    ticker.start()
    return {"started": True}

@app.post("/tick/stop")
async def tick_stop():
    ticker.stop()
    return {"stopped": True}

# --- trade log tail (simple, CSV text back) ---
@app.get("/logs/trades/tail")
async def tail_trades(n: int = Query(50, ge=1, le=1000), path: str = "logs/trade_log.csv"):
    p = pathlib.Path(path)
    if not p.exists():
        return {"lines": []}
    # quick tail without loading whole file
    try:
        with p.open("rb") as f:
            f.seek(0, 2)
            size = f.tell()
            block = 4096
            data = b""
            while size > 0 and data.count(b"\n") <= n:
                step = min(block, size)
                size -= step
                f.seek(size)
                data = f.read(step) + data
        lines = [ln.decode("utf-8", "ignore").rstrip("\n") for ln in data.splitlines()[-n:]]
    except Exception:
        lines = p.read_text(errors="ignore").splitlines()[-n:]
    return {"lines": lines}

# --- mount /web and serve it at root ---
app.mount("/web", StaticFiles(directory="web", html=True), name="web")

from fastapi import Query
from engine.fs import list_tree as _fs_list, get_file as _fs_get

@app.get("/fs/tree")
async def fs_tree(subdir: str = Query(".", description="relative to ~/AI")):
    return _fs_list(subdir)

@app.get("/fs/get")
async def fs_get(path: str = Query(..., description="relative path under ~/AI")):
    return _fs_get(path)
