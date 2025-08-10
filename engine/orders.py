from typing import Dict, Any, Tuple
from .state import load_state, save_state
from .executor import place_order
from . import risk

def _pos(st) -> Tuple[float,float]:
    p = st.get("positions", {}).get("BTCUSDT", {"qty":0.0,"avg_price":0.0})
    return float(p.get("qty",0.0)), float(p.get("avg_price",0.0))

def preview(side: str, fraction: float, price: float) -> Dict[str, Any]:
    st = load_state()
    side = str(side).upper()
    fraction = max(0.0, min(1.0, float(fraction)))
    qty, avg = _pos(st)

    # Risk gate only needed pre-BUY
    ok, why = (True, "ok")
    if side == "BUY":
        ok, why = risk.enforce_pre_trade(st, side=side, fraction=fraction, price=price)

    info = {
        "side": side,
        "fraction": fraction,
        "price": price,
        "balance": st.get("balance", 0.0),
        "pos_qty": qty,
        "pos_avg": avg,
        "risk_ok": ok,
        "risk_reason": why,
    }

    if side == "BUY" and ok:
        spend = st.get("balance", 0.0) * fraction
        info["est_qty"] = spend / float(price) if price > 0 else 0.0
    elif side in {"SELL","EXIT"}:
        use_qty = qty if side == "EXIT" else qty * fraction
        info["est_qty"] = max(0.0, min(qty, use_qty))
        info["est_proceeds"] = info["est_qty"] * float(price)
    return info

def submit(side: str, fraction: float, price: float, plugin: str = "manual") -> Dict[str, Any]:
    st = load_state()
    side = str(side).upper()
    fraction = max(0.0, min(1.0, float(fraction)))
    res = place_order(st, side=side, price=price, fraction=fraction, plugin=plugin)
    save_state(st)
    return res
