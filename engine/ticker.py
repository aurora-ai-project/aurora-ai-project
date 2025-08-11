import asyncio, time
from typing import Dict, Any
from .state import load_state, save_state
from .loader import load_plugins, get_loaded_modules
from .datafeed import FEED
from .executor import place_order

_config = {"enabled": True, "interval": 1.0}
_task = None

def _safe_call(fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except Exception as e:
        return {"error": str(e)}

async def tick_once() -> Dict[str, Any]:
    load_plugins()
    mods = get_loaded_modules()
    state = load_state()
    ctx = FEED.next()
    results = {}
    for m in mods:
        on_tick = getattr(m, "on_tick", None)
        name = getattr(m, "REGISTER_NAME", m.__name__)
        if callable(on_tick):
            res = _safe_call(on_tick, state, ctx)
            # honor trading signals if present
            if isinstance(res, dict) and "signal" in res:
                sig = str(res["signal"]).upper()
                stake = float(res.get("stake", 0.10))
                if sig in {"BUY","SELL","EXIT"}:
                    trade = place_order(state, side=sig, price=ctx["price"], fraction=1.0 if sig=="EXIT" else stake, plugin=name)
                    res["trade_result"] = trade
            results[name] = res
    # update mark-to-market
    pos = state.setdefault("positions", {}).setdefault("BTCUSDT", {"qty": 0.0, "avg_price": 0.0})
    qty = float(pos.get("qty", 0.0))
    avg = float(pos.get("avg_price", 0.0))
    mtm = (ctx["price"] - avg) * qty
    state["unrealized_pnl"] = round(mtm, 2)

    state["last_tick"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    state["last_ctx"] = ctx
    state["last_tick_results"] = results
    save_state(state)
    return {"tick_time": state["last_tick"], "ctx": ctx, "results": results}

async def _loop():
    while True:
        if _config["enabled"]:
            await tick_once()
        await asyncio.sleep(max(0.05, float(_config["interval"])))

def get_config() -> Dict[str, Any]:
    return dict(_config)

def set_config(enabled: bool | None = None, interval: float | None = None) -> Dict[str, Any]:
    if enabled is not None:
        _config["enabled"] = bool(enabled)
    if interval is not None:
        try:
            _config["interval"] = max(0.05, float(interval))
        except Exception:
            pass
    return get_config()

def start_background(loop: asyncio.AbstractEventLoop) -> asyncio.Task:
    global _task
    if _task and not _task.done():
        return _task
    _task = loop.create_task(_loop())
    return _task

def stop_background():
    global _task
    if _task and not _task.done():
        _task.cancel()
        _task = None