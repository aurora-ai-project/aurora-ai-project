from ..engine.strategy_sdk import Strategy
from ..engine.types import StrategyVote
class MomentumStrategy(Strategy):
    def __init__(self, window:int=10):
        super().__init__(f"MOM_{window}")
        self.buf=[]; self.window=window
    def on_price(self, price: float) -> StrategyVote:
        self.buf.append(price); 
        if len(self.buf)>self.window: self.buf=self.buf[-self.window:]
        if len(self.buf)<self.window: return StrategyVote(name=self.name, bias=0.0, confidence=0.0, note="warming")
        slope=(self.buf[-1]-self.buf[0])/max(self.buf[0],1e-9)
        bias=max(min(slope*5,1.0),-1.0)
        conf=min(abs(slope)*10,1.0)
        return StrategyVote(name=self.name, bias=bias, confidence=conf, note=f"slope={slope:.5f}")
