import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import List
from .settings import SYMBOL, INTERVAL_SEC, LOGS, STATE, START_EQUITY, STAKE_FRACTION, MAX_PER_TRADE, RESERVE_FRACTION, SL_PCT, TP_PCT, MAX_POSITIONS, MAX_DD_PCT
from .types import State, Position, StrategyVote, Decision
from .pricefeed import stream_prices
from .atomic import atomic_write_json, atomic_append_csv
from .voting import combine_votes
from ..plugins.ema import EMAStrategy
from ..plugins.rsi import RSIStrategy
from ..plugins.momentum import MomentumStrategy

WS_CLIENTS = set()  # populated by API via import

def now(): return datetime.utcnow().replace(tzinfo=timezone.utc)

class Trader:
    def __init__(self):
        self.state = State(equity=START_EQUITY, cash=START_EQUITY, positions=[], peak_equity=START_EQUITY, halted=False)
        self.strats = [EMAStrategy(8,21), RSIStrategy(30,70,14), MomentumStrategy(12)]
        LOGS.mkdir(parents=True, exist_ok=True)
        atomic_write_json(STATE, self.state.model_dump())

    async def push_ws(self, kind:str, payload:dict):
        dead=[]
        for ws in list(WS_CLIENTS):
            try:
                await ws.send_json({"ts": now().isoformat(), "kind": kind, "payload": payload})
            except Exception:
                dead.append(ws)
        for d in dead: WS_CLIENTS.discard(d)

    def equity(self, mark: float)->float:
        return self.state.cash + sum(p.qty*mark for p in self.state.positions)

    def risk_ok(self, mark: float)->bool:
        eq=self.equity(mark); self.state.equity=eq; self.state.peak_equity=max(self.state.peak_equity, eq)
        if eq < START_EQUITY*(1-MAX_DD_PCT): self.state.halted=True
        return not self.state.halted

    def sizing(self, mark: float)->float:
        free=self.state.cash - max(0.0, self.equity(mark)*RESERVE_FRACTION - sum(p.qty*mark for p in self.state.positions))
        size=min(max(free*STAKE_FRACTION, 0.0), MAX_PER_TRADE)
        return max(size, 0.0)

    def close_signals(self, mark:float)->List[Position]:
        exits=[]
        for p in self.state.positions:
            pnl=(mark - p.entry)*p.qty
            if pnl <= -SL_PCT*p.stake or pnl >= TP_PCT*p.stake:
                exits.append(p)
        return exits

    def apply_fill(self, side:str, qty:float, price:float, stake:float, note:str):
        if side=='BUY':
            self.state.cash -= qty*price
            self.state.positions.append(Position(symbol=SYMBOL, qty=qty, entry=price, stake=stake, ts=now()))
        else:
            if not self.state.positions: return
            p=self.state.positions.pop(0)
            pnl=(price - p.entry)*p.qty
            self.state.cash += p.qty*price
        atomic_write_json(STATE, self.state.model_dump())
        atomic_append_csv(Path(LOGS/'trade_log.csv'), [now().isoformat(), SYMBOL, side, qty, price, stake, note])

    async def on_bar(self, ts, price: float):
        eq=self.equity(price)
        if not self.risk_ok(price):
            await self.push_ws("halt", {"equity":eq}); return
        votes=[s.on_price(price) for s in self.strats]  # type: List[StrategyVote]
        decision=combine_votes(votes)                   # type: Decision
        await self.push_ws("votes", {"price":price, "decision":decision.model_dump()})
        for p in self.close_signals(price):
            self.apply_fill('SELL', p.qty, price, p.stake, "SL/TP exit")
            await self.push_ws("fill", {"side":"SELL","qty":p.qty,"price":price,"note":"SL/TP"})
        if decision.action=='BUY' and len(self.state.positions)<MAX_POSITIONS:
            stake=self.sizing(price)
            if stake>0:
                qty=stake/price
                self.apply_fill('BUY', qty, price, stake, decision.reason)
                await self.push_ws("fill", {"side":"BUY","qty":qty,"price":price,"note":decision.reason})
        elif decision.action=='SELL' and self.state.positions:
            p=self.state.positions[0]
            self.apply_fill('SELL', p.qty, price, p.stake, decision.reason)
            await self.push_ws("fill", {"side":"SELL","qty":p.qty,"price":price,"note":decision.reason})

    async def run(self):
        async for bar in stream_prices(SYMBOL, INTERVAL_SEC):
            await self.on_bar(bar.ts, bar.price)

TRADER = Trader()

async def main():
    await TRADER.run()

if __name__=="__main__":
    asyncio.run(main())
