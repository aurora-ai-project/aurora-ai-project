from collections import deque
from typing import Dict, Deque
class Rolling:
    def __init__(self, n:int): self.n=n; self.buf:Deque[float]=deque(maxlen=n)
    def push(self, x:float): self.buf.append(x)
    def mean(self): return sum(self.buf)/len(self.buf) if self.buf else 0.0
def ema(prev, price, period):
    k=2/(period+1)
    return price if prev is None else (price*k + prev*(1-k))
def rsi(state:Dict[str,float], price:float, period:int=14):
    if 'avg_gain' not in state:
        state.update(avg_gain=0.0, avg_loss=0.0, last=price); return 50.0
    change=price - state['last']; state['last']=price
    gain=max(change,0.0); loss=max(-change,0.0)
    ag=state['avg_gain']* (period-1)/period + gain/period
    al=state['avg_loss']* (period-1)/period + loss/period
    state['avg_gain'], state['avg_loss']=ag,al
    if al==0: return 100.0
    rs=ag/al
    return 100 - (100/(1+rs))
