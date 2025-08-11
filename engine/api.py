import asyncio
from fastapi import FastAPI
from engine.trader import Trader

app = FastAPI()
trader = Trader(interval_seconds=1.0)

@app.on_event("startup")
async def start_bg():
    asyncio.create_task(trader.tick_loop())  # run forever in background

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/tick/once")
async def tick_once():
    await trader.tick_once()                 # <- awaited (no warnings)
    return {"ok": True}
