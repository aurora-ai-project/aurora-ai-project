import asyncio
import httpx, time

BASE = "https://api.binance.com"
def get_latest_close(symbol="BTCUSDT", interval="1m"):
    url = f"{BASE}/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": 1}
    with httpx.Client(timeout=5.0) as c:
        r = c.get(url, params=params)
        r.raise_for_status()
        k = r.json()[0]
        # open time, open, high, low, close, volume, close time, ...
        close = float(k[4]); t_close = int(k[6])//1000
        return {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t_close)), "price": round(close,2)}