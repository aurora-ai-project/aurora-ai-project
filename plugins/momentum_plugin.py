import asyncio
REGISTER_NAME = "momentum_plugin"
def on_tick(state, ctx):
    return {"momentum": "hold", "price": ctx["price"]}