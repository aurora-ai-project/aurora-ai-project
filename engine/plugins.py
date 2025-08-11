import importlib, pkgutil, inspect, sys
from dataclasses import dataclass
from typing import Protocol, Literal, Dict, List

Action = Literal["buy","sell","hold"]

class Strategy(Protocol):
    name: str
    def on_price(self, price: float) -> None: ...
    def vote(self) -> Dict[str, float]: ...  # {"confidence": 0..1, "bias": -1..1}

@dataclass
class Loaded:
    name: str
    obj: Strategy

_cache: List[Loaded] | None = None

def load_plugins(pkg_name: str = "plugins") -> List[Loaded]:
    global _cache
    if _cache is not None:
        return _cache
    loaded: List[Loaded] = []
    pkg = importlib.import_module(pkg_name)
    for m in pkgutil.iter_modules(pkg.__path__, pkg_name + "."):
        mod = importlib.import_module(m.name)
        for _, cls in inspect.getmembers(mod, inspect.isclass):
            if getattr(cls, "__module__", "").startswith(pkg_name) and hasattr(cls, "vote") and hasattr(cls, "on_price"):
                try:
                    obj = cls()
                    loaded.append(Loaded(getattr(obj,"name",cls.__name__), obj))
                except Exception:
                    pass
    _cache = loaded
    return loaded

def reload_plugins(pkg_name: str = "plugins") -> List[Loaded]:
    global _cache
    _cache = None
    # drop plugin modules from sys.modules
    prefix = pkg_name + "."
    for k in list(sys.modules.keys()):
        if k == pkg_name or k.startswith(prefix):
            sys.modules.pop(k, None)
    importlib.invalidate_caches()
    return load_plugins(pkg_name)

def combine_votes(votes: List[Dict[str, float]]) -> Dict[str, float]:
    score = 0.0
    conf_sum = 0.0
    for v in votes:
        c = max(0.0, min(1.0, float(v.get("confidence",0))))
        b = max(-1.0, min(1.0, float(v.get("bias",0))))
        score += c * b
        conf_sum += c
    action: Action = "hold"
    if score > 0.1: action = "buy"
    elif score < -0.1: action = "sell"
    return {"action": action, "score": score, "confidence": conf_sum/len(votes) if votes else 0.0}
