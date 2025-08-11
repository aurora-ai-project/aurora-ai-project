import os, csv, time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional, Literal

Action = Literal["buy","sell","hold"]

LOG_PATH = Path("logs/trade_log.csv")
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
if not LOG_PATH.exists():
    LOG_PATH.write_text("ts,action,price,qty,balance,position,size,avg_price,unrealized_pnl,realized_pnl\n")

@dataclass
class Position:
    size: float = 0.0         # +long, -short
    avg_price: float = 0.0

@dataclass
class Account:
    balance: float = float(os.getenv("AURORA_BALANCE", "1000"))
    pos: Position = field(default_factory=Position)
    realized_pnl: float = 0.0
    sl_pct: float = float(os.getenv("AURORA_SL_PCT", "0.02"))   # 2%
    tp_pct: float = float(os.getenv("AURORA_TP_PCT", "0.03"))   # 3%
    stake_frac: float = float(os.getenv("AURORA_STAKE_FRAC", "0.10"))  # 10% of balance

    def position_value(self, price: float) -> float:
        return self.pos.size * price

    def unrealized(self, price: float) -> float:
        if self.pos.size == 0: return 0.0
        side = 1.0 if self.pos.size > 0 else -1.0
        return side * abs(self.pos.size) * (price - self.pos.avg_price)

    def apply_sl_tp(self, price: float) -> Optional[Action]:
        if self.pos.size == 0: return None
        side = "buy" if self.pos.size > 0 else "sell"
        # SL/TP thresholds based on entry avg_price
        if self.pos.size > 0:
            if price <= self.pos.avg_price * (1.0 - self.sl_pct): return "sell"  # stop long
            if price >= self.pos.avg_price * (1.0 + self.tp_pct): return "sell"  # take profit long
        else:  # short
            if price >= self.pos.avg_price * (1.0 + self.sl_pct): return "buy"   # stop short
            if price <= self.pos.avg_price * (1.0 - self.tp_pct): return "buy"   # take profit short
        return None

    def _log(self, action: Action, price: float, qty: float) -> None:
        row = {
            "ts": int(time.time()),
            "action": action,
            "price": round(price, 8),
            "qty": round(qty, 8),
            "balance": round(self.balance, 8),
            "position": round(self.pos.size, 8),
            "size": round(abs(self.pos.size), 8),
            "avg_price": round(self.pos.avg_price, 8),
            "unrealized_pnl": 0.0,  # filled by caller if needed
            "realized_pnl": round(self.realized_pnl, 8),
        }
        with LOG_PATH.open("a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=row.keys())
            w.writerow(row)

    def _avg_in(self, old_size: float, old_avg: float, add_size: float, price: float) -> float:
        # Weighted average price for increasing a position on same side
        notional = old_avg * abs(old_size) + price * abs(add_size)
        total = abs(old_size) + abs(add_size)
        return notional / total if total > 0 else price

    def execute(self, action: Action, price: float) -> dict:
        # Determine qty by stake fraction (market order, 1x)
        if action == "hold": 
            self._log(action, price, 0.0)
            return self.status(price)

        qty_value = max(0.0, self.balance * self.stake_frac)
        qty = 0.0 if price <= 0 else qty_value / price
        if qty == 0.0:
            self._log("hold", price, 0.0)
            return self.status(price)

        if action == "buy":
            # If currently short, reduce/flip; else increase long
            if self.pos.size < 0:
                cover = min(abs(self.pos.size), qty)
                pnl = (self.pos.avg_price - price) * cover  # short PnL
                self.realized_pnl += pnl
                self.balance += pnl
                self.pos.size += cover
                qty -= cover
            if qty > 0:
                new_avg = self._avg_in(self.pos.size, self.pos.avg_price, qty, price) if self.pos.size > 0 else price
                self.pos.avg_price = new_avg
                self.pos.size += qty
                self.balance -= qty * price
            self._log("buy", price, qty)
        elif action == "sell":
            # If currently long, reduce/flip; else increase short
            if self.pos.size > 0:
                reduce = min(self.pos.size, qty)
                pnl = (price - self.pos.avg_price) * reduce  # long PnL
                self.realized_pnl += pnl
                self.balance += pnl
                self.pos.size -= reduce
                qty -= reduce
            if qty > 0:
                new_avg = self._avg_in(self.pos.size, self.pos.avg_price, -qty, price) if self.pos.size < 0 else price
                self.pos.avg_price = new_avg
                self.pos.size -= qty
                self.balance += qty * price
            self._log("sell", price, qty)
        return self.status(price)

    def status(self, price: float) -> dict:
        return {
            "balance": round(self.balance, 8),
            "position": round(self.pos.size, 8),
            "avg_price": round(self.pos.avg_price, 8),
            "unrealized_pnl": round(self.unrealized(price), 8),
            "realized_pnl": round(self.realized_pnl, 8),
        }

account = Account()
