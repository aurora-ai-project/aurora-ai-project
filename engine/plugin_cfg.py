import asyncio
from .state import load_state, save_state

DEFAULT_CAP = 10.0  # % of cash for BUY per plugin before global risk

def get_caps():
    st = load_state()
    caps = st.get("plugin_caps", {})
    return caps

def set_cap(name: str, pct: float):
    st = load_state()
    caps = st.setdefault("plugin_caps", {})
    caps[name] = float(max(0.1, min(100.0, pct)))
    save_state(st)
    return caps

def resolve_cap(name: str) -> float:
    caps = get_caps()
    return float(caps.get(name, DEFAULT_CAP))