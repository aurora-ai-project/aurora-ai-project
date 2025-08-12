from ..engine.strategy_sdk import Strategy
from ..engine.types import StrategyVote
from ..engine.indicators import rsi
class RSIStrategy(Strategy):
    def __init__(self, low=30, high=70, period=14):
        super().__init__(f"RSI_{period}_{low}_{high}")
        self.state={}; self.low=low; self.high=high; self.period=period
    def on_price(self, price: float) -> StrategyVote:
        v=rsi(self.state, price, self.period)
        if v<self.low: bias=+1.0; conf=min((self.low-v)/self.low,1.0)
        elif v>self.high: bias=-1.0; conf=min((v-self.high)/(100-self.high),1.0)
        else: bias=0.0; conf=0.2
        return StrategyVote(name=self.name, bias=bias, confidence=conf, note=f"rsi={v:.2f}")
