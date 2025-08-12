import asyncio, random, math
from datetime import datetime, timezone
from typing import AsyncIterator
import httpx
from .types import Bar
async def fetch_binance_price(symbol: str) -> float:
    url=f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    async with httpx.AsyncClient(timeout=5) as client:
        r=await client.get(url)
        r.raise_for_status()
        return float(r.json()['price'])
async def stream_prices(symbol: str, interval: float) -> AsyncIterator[Bar]:
    price=None; drift=0.0
    while True:
        ts=datetime.utcnow().replace(tzinfo=timezone.utc)
        try:
            price = await fetch_binance_price(symbol)
        except Exception:
            price = (price or 50000.0) * math.exp(random.uniform(-0.002,0.002)) + drift
            drift *= 0.95
        yield Bar(ts=ts, symbol=symbol, price=float(price))
        await asyncio.sleep(interval)
