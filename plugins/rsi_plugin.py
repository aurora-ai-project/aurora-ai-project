import asyncio
REGISTER_NAME = "rsi_plugin"
def on_tick(state, ctx):
    c = int(state.get("rsi_ticks", 0)) + 1
    state["rsi_ticks"] = c
    return {"price": ctx["price"], "ticks_seen": c}