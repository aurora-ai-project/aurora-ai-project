import asyncio
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
from typing import List
from .state import load_state, save_state

PLUGINS_DIR = Path("plugins")
_LOADED_MODS = []

def discover_plugins() -> List[Path]:
    PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(p for p in PLUGINS_DIR.glob("*.py") if p.name not in {"__init__.py"} and not p.name.startswith("_"))

def _safe_call(fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except Exception as e:
        return {"error": str(e)}

def load_plugins() -> list:
    global _LOADED_MODS
    loaded = []
    state = load_state()
    mods = []
    for path in discover_plugins():
        mod_name = f"plugins.{path.stem}"
        spec = spec_from_file_location(mod_name, path)
        if not spec or not spec.loader:
            continue
        mod = module_from_spec(spec)
        spec.loader.exec_module(mod)
        name = getattr(mod, "REGISTER_NAME", path.stem)
        if name not in state["plugins"]:
            state["plugins"].append(name)
        # optional on_load(state)
        if hasattr(mod, "on_load"):
            res = _safe_call(mod.on_load, state)
            state.setdefault("plugin_init", {})[name] = res
        mods.append(mod)
        loaded.append(name)
    save_state(state)
    _LOADED_MODS = mods
    return loaded

def get_loaded_modules():
    return list(_LOADED_MODS)

def plugin_spec():
    return {
        "REGISTER_NAME": "required:str",
        "on_load(state)": "optional -> dict",
        "on_tick(state, ctx)": "optional -> dict   ctx={ts,tick,price}",
        "on_event(state, event)": "optional -> dict",
    }