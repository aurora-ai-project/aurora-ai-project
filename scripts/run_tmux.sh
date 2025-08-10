#!/usr/bin/env bash
set -euo pipefail
cd /home/aurora/AI
[ -f .env ] && set -a && . ./.env && set +a
tmux kill-server 2>/dev/null || true
tmux new-session -d -s aurora "bash -lc 'cd /home/aurora/AI && [ -f .env ] && set -a && . ./.env && set +a && source venv/bin/activate && uvicorn engine.api:app --host 127.0.0.1 --port 8000'"
tmux split-window -h -t aurora "bash -lc 'cd /home/aurora/AI && [ -f .env ] && set -a && . ./.env && set +a && source venv/bin/activate && python - <<\"PY\"
import time
from engine.ticker import tick_once, set_config
set_config(enabled=True, interval=1)
while True:
    try:
        tick_once()
    except Exception as e:
        print(\"[ticker] error:\", e)
    time.sleep(1)
PY'"
tmux attach -t aurora
