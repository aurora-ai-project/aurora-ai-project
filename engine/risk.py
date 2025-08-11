import asyncio
from typing import Tuple

DEFAULTS = {
    "max_drawdown_pct": 15.0,     # halt sells/buys if equity < (1-maxDD)*initial
    "stake_cap_pct": 10.0,        # max fraction of cash per BUY
    "min_cash_reserve_pct": 50.0, # always leave this % of cash untouched
    "sl_pct": 20.0,               # stop-loss: if loss >= 20% vs avg, exit all
    "tp_pct": 30.0,               # take-profit: if gain >= 30% vs avg, take 25%
    "tp_partial_pct": 25.0        # % of position to take when TP hits
}

def get_config(state: dict) -> dict:
    rc = dict(DEFAULTS)
    rc.update(state.get("risk", {}))
    return rc

def set_config(state: dict, **kwargs) -> dict:
    rc = get_config(state)
    for k,v in kwargs.items():
        if v is None: continue
        if k in DEFAULTS:
            try: rc[k] = float(v)
            except: pass
    state["risk"] = rc
    return rc

def _equity(state: dict, mkt_price: float) -> float:
    bal = float(state.get("balance", 0.0))
    pos = state.get("positions", {}).get("BTCUSDT", {"qty":0.0,"avg_price":0.0})
    qty = float(pos.get("qty",0.0)); avg = float(pos.get("avg_price",0.0))
    return bal + (mkt_price - avg) * qty

def enforce_pre_trade(state: dict, *, side: str, fraction: float, price: float) -> Tuple[bool,str]:
    rc = get_config(state)
    state.setdefault("initial_balance", float(state.get("balance", 1000.0)))
    initial = float(state["initial_balance"])
    eq = _equity(state, price)
    # drawdown halt
    if eq < initial * (1.0 - rc["max_drawdown_pct"]/100.0):
        return False, "max_drawdown_reached"

    if side == "BUY":
        # cap stake, and enforce cash reserve
        cap = rc["stake_cap_pct"]/100.0
        fraction = min(fraction, cap)
        bal = float(state.get("balance", 0.0))
        spend = bal * fraction
        reserve_min = bal * (rc["min_cash_reserve_pct"]/100.0)
        if bal - spend < reserve_min:
            return False, "min_cash_reserve"
    return True, "ok"

def auto_risk_actions(state: dict, *, price: float):
    pos = state.get("positions", {}).get("BTCUSDT", {"qty":0.0,"avg_price":0.0})
    qty = float(pos.get("qty",0.0)); avg = float(pos.get("avg_price",0.0))
    if qty <= 0 or avg <= 0: return None
    rc = get_config(state)
    change = (price - avg) / avg * 100.0
    if change <= -rc["sl_pct"]:
        return {"signal":"EXIT", "reason":"SL"}
    if change >= rc["tp_pct"]:
        return {"signal":"SELL", "stake": rc["tp_partial_pct"]/100.0, "reason":"TP"}
    return None