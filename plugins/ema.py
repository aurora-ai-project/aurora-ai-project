from ..engine.strategy_sdk import Strategy
from ..engine.types import StrategyVote
from ..engine.indicators import ema
class EMAStrategy(Strategy):
    def __init__(self, fast:int=12, slow:int=26):
        super().__init__(f"EMA_{fast}_{slow}")
        self.fast=None; self.slow=None; self.p_fast=fast; self.p_slow=slow
    def on_price(self, price: float) -> StrategyVote:
        self.fast=ema(self.fast, price, self.p_fast)
        self.slow=ema(self.slow, price, self.p_slow)
        if self.fast is None or self.slow is None:
            return StrategyVote(name=self.name, bias=0.0, confidence=0.0, note="warming")
        diff=(self.fast - self.slow)/max(self.slow,1e-9)
        bias= max(min(diff*5, 1.0), -1.0)
        conf= min(abs(diff)*20, 1.0)
        return StrategyVote(name=self.name, bias=bias, confidence=conf, note=f"diff={diff:.5f}")
