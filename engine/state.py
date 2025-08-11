import asyncio
from pathlib import Path
import json, time

STATE_FILE = Path("logs/state.json")

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text() or "{}")
    return {"balance": 1000.0, "plugins": [], "last_heartbeat": None}

def save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state["last_heartbeat"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    STATE_FILE.write_text(json.dumps(state, indent=2))