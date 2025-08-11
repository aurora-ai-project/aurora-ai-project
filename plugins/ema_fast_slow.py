class EMA:
    def __init__(self, period: int):
        self.p = max(1, int(period))
        self.k = 2.0/(self.p+1.0)
        self.v = None
    def update(self, price: float) -> float:
        self.v = (price if self.v is None else (price - self.v)*self.k + self.v)
        return self.v

class EMAFastSlow:
    name = "ema_fast_slow"
    def __init__(self):
        self.fast = EMA(12)
        self.slow = EMA(26)
        self.bias = 0.0
        self.conf = 0.0
    def on_price(self, price: float) -> None:
        f = self.fast.update(price)
        s = self.slow.update(price)
        if f is None or s is None: 
            self.bias, self.conf = 0.0, 0.0
            return
        spread = f - s
        self.bias = 1.0 if spread > 0 else (-1.0 if spread < 0 else 0.0)
        # confidence grows with magnitude of spread relative to price
        self.conf = min(1.0, abs(spread) / max(1e-6, price*0.002))
    def vote(self) -> dict:
        return {"bias": float(self.bias), "confidence": float(self.conf)}
