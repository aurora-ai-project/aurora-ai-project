from pathlib import Path
from datetime import datetime
import csv

TRADE_LOG = Path("logs/trade_log.csv")
SYMBOL = "BTCUSDT"

def _ensure_state(state: dict):
    state.setdefault("balance", 1000.0)
    state.setdefault("positions", {})
    state["positions"].setdefault(SYMBOL, {"qty": 0.0, "avg_price": 0.0})

def _log_trade(ts, plugin, side, price, qty, cash_delta, balance, pos_qty, avg_price):
    TRADE_LOG.parent.mkdir(parents=True, exist_ok=True)
    write_header = not TRADE_LOG.exists()
    with TRADE_LOG.open("a", newline="") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(["ts","symbol","plugin","side","price","qty","cash_delta","balance_after","pos_qty_after","avg_price_after"])
        w.writerow([ts, SYMBOL, plugin, side, f"{price:.2f}", f"{qty:.8f}", f"{cash_delta:.2f}", f"{balance:.2f}", f"{pos_qty:.8f}", f"{avg_price:.2f}"])

def place_order(state: dict, *, side: str, price: float, fraction: float, plugin: str):
    """
    side: 'BUY' | 'SELL' | 'EXIT'
    fraction: portion of balance (BUY) or position (SELL) to use, 0..1
    """
    _ensure_state(state)
    ts = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    bal = float(state["balance"])
    pos = state["positions"][SYMBOL]
    qty = float(pos["qty"])
    avg = float(pos["avg_price"])

    side = side.upper()
    fraction = max(0.0, min(1.0, float(fraction)))

    if side == "BUY":
        spend = bal * fraction
        if spend <= 0.0:
            return {"ok": False, "reason": "no_cash"}
        buy_qty = spend / float(price)
        new_qty = qty + buy_qty
        new_avg = ((qty * avg) + spend) / new_qty if new_qty > 0 else 0.0
        bal -= spend
        pos["qty"], pos["avg_price"] = new_qty, new_avg
        state["balance"] = round(bal, 2)
        _log_trade(ts, plugin, "BUY", price, buy_qty, -spend, bal, new_qty, new_avg)
        return {"ok": True, "side": "BUY", "qty": buy_qty}

    sell_qty = qty if side == "EXIT" else qty * fraction
    sell_qty = min(qty, sell_qty)
    if sell_qty <= 0.0:
        return {"ok": False, "reason": "no_position"}
    proceeds = sell_qty * float(price)
    # realized PnL tracking (optional; stored on state)
    basis = sell_qty * avg
    realized = proceeds - basis
    state["realized_pnl"] = float(state.get("realized_pnl", 0.0)) + realized

    new_qty = qty - sell_qty
    new_avg = avg if new_qty > 0 else 0.0
    bal += proceeds
    pos["qty"], pos["avg_price"] = new_qty, new_avg
    state["balance"] = round(bal, 2)
    _log_trade(ts, plugin, "SELL" if side != "EXIT" else "EXIT", price, sell_qty, proceeds, bal, new_qty, new_avg)
    return {"ok": True, "side": "SELL", "qty": sell_qty}
