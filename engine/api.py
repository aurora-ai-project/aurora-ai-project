import os
from fastapi import FastAPI
from .ticker import ticker

app = FastAPI(title="Aurora Engine API")

@app.on_event("startup")
async def _startup():
    if os.getenv("AURORA_AUTOSTART", "1") == "1":
        ticker.start()

@app.get("/health")
async def health():
    return {"ok": True}

@app.get("/status")
async def status():
    running = bool(ticker._task and not ticker._task.done())
    return {"running": running, "last_tick": ticker.last_tick, "count": ticker.count}

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
