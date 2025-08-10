REGISTER_NAME = "ema_plugin"
def on_load(state):
    state.setdefault("ema_seen", 0)
    return {"status": "loaded"}
def on_tick(state, ctx):
    state["ema_seen"] += 1
    even = (ctx["tick"] % 2) == 0
    if even:
        return {"signal": "BUY", "stake": 0.10, "note": "even tick buy", "price": ctx["price"], "tick": ctx["tick"]}
    else:
        return {"signal": "SELL", "stake": 0.10, "note": "odd tick sell", "price": ctx["price"], "tick": ctx["tick"]}
