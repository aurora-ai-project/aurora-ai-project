from collections import deque
class MomoSimple:
    name = "momentum_simple"
    def __init__(self):
        self.w = deque(maxlen=10)
        self.bias = 0.0
        self.conf = 0.0
    def on_price(self, price: float) -> None:
        self.w.append(float(price))
        if len(self.w) < 3:
            self.bias, self.conf = 0.0, 0.0
            return
        # simple slope
        slope = self.w[-1] - self.w[0]
        self.bias = 1.0 if slope > 0 else (-1.0 if slope < 0 else 0.0)
        self.conf = min(1.0, abs(slope) / max(1e-6, self.w[0]*0.003))
    def vote(self) -> dict:
        return {"bias": float(self.bias), "confidence": float(self.conf)}
