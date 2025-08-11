import asyncio
REGISTER_NAME = "ai_plugin"
from engine.ai_agent import step, load, save, set_eps, set_stake

def on_load(state):
    load()
    state.setdefault("ai", {"history": [], "last_equity": None, "eps": 0.10})
    return {"status":"loaded"}

def on_tick(state, ctx):
    price = float(ctx["price"])
    pos = state.setdefault("positions", {}).setdefault("BTCUSDT", {"qty":0.0,"avg_price":0.0})
    qty = float(pos.get("qty",0.0))
    cash = float(state.get("balance", 0.0))
    equity = cash + qty * price

    last_eq = state["ai"].get("last_equity")
    if last_eq is None:
        reward = 0.0
    else:
        reward = equity - float(last_eq)
    state["ai"]["last_equity"] = equity

    hist = state["ai"].setdefault("history", [])
    hist.append(price)
    if len(hist) > 500:
        del hist[:len(hist)-500]

    out = step(hist, qty, cash, price, reward)
    act = out["action"]; stake = out["stake"]
    if act == "HOLD":
        return {"note":"hold", **out}
    sig = "BUY" if act=="BUY" else "SELL"
    return {"signal": sig, "stake": stake, **out}