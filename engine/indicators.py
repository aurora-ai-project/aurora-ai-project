import asyncio
from collections import deque
from math import isnan

# Simple rolling EMA and RSI (close-only)
def ema(prev, price, period):
    k = 2.0 / (period + 1.0)
    return (price * k) + (prev * (1 - k)) if prev is not None else price

def rsi_calc(closes, period=14):
    if len(closes) < period + 1: return None
    gains = 0.0; losses = 0.0
    for i in range(1, period + 1):
        delta = closes[-i] - closes[-i-1]
        if delta >= 0: gains += delta
        else: losses -= delta
    if losses == 0: return 100.0
    rs = (gains / period) / (losses / period)
    return 100.0 - (100.0 / (1.0 + rs))

def update_indicators(state: dict, price: float):
    ind = state.setdefault("indicators", {})
    ind["ema12"] = ema(ind.get("ema12"), price, 12)
    ind["ema26"] = ema(ind.get("ema26"), price, 26)
    # keep a tiny close buffer for RSI
    buf = state.setdefault("closes", [])
    buf.append(price)
    if len(buf) > 50: del buf[:len(buf)-50]
    r = rsi_calc(buf, 14)
    if r is not None and not isnan(r): ind["rsi14"] = r
    state["indicators"] = ind
    return ind

def readiness_snapshot(state: dict, price: float):
    ind = state.get("indicators", {})
    ema12 = ind.get("ema12"); ema26 = ind.get("ema26"); rsi = ind.get("rsi14")
    # Trend readiness: normalized EMA spread
    trend = None; trend_strength = None
    if ema12 is not None and ema26 is not None and price:
        spread = (ema12 - ema26)
        trend = "up" if spread > 0 else "down" if spread < 0 else "flat"
        trend_strength = round(abs(spread) / price, 4)

    # RSI proximity to edges (30/70)
    rsi_near = None
    if rsi is not None:
        to30 = abs(rsi - 30.0); to70 = abs(rsi - 70.0)
        rsi_near = {"value": round(rsi,2), "to30": round(to30,2), "to70": round(to70,2)}

    # Position presence
    pos = state.get("positions", {}).get("BTCUSDT", {"qty":0.0,"avg_price":0.0})
    in_pos = (float(pos.get("qty",0.0)) > 0.0)

    return {
        "trend": trend,
        "trend_strength": trend_strength,
        "ema12": round(ema12,2) if ema12 is not None else None,
        "ema26": round(ema26,2) if ema26 is not None else None,
        "rsi": rsi_near,
        "in_position": in_pos,
    }