import asyncio
import time, random
from .binance import get_latest_close

class PriceFeed:
    def __init__(self, symbol="BTCUSDT", start=30000.0, drift=0.0, vol=25.0, seed=42):
        random.seed(seed)
        self.symbol = symbol
        self.price = float(start)
        self.drift = float(drift)
        self.vol = float(vol)
        self.t = 0

    def _fallback(self):
        self.t += 1
        shock = random.uniform(-self.vol, self.vol)
        self.price = max(1.0, self.price + self.drift + shock)
        return {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "tick": self.t,
            "price": round(self.price, 2),
            "symbol": self.symbol,
            "source": "fallback",
        }

    def next(self):
        # Try Binance; on any error, fallback
        try:
            data = get_latest_close(self.symbol, "1m")
            self.t += 1
            self.price = data["price"]
            return {
                "ts": data["ts"],
                "tick": self.t,
                "price": self.price,
                "symbol": self.symbol,
                "source": "binance",
            }
        except Exception:
            return self._fallback()

FEED = PriceFeed()