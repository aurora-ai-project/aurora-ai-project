#!/usr/bin/env bash
set -euo pipefail
tmux kill-server 2>/dev/null || true
BASE="cd /home/aurora/AI && source venv/bin/activate"
tmux new -d -s aurora_backend "$BASE && uvicorn engine.api:app --host 0.0.0.0 --port 8000"
tmux new -d -s aurora_trader  "$BASE && python -m engine.trader"
command -v nginx >/dev/null 2>&1 && tmux new -d -s aurora_nginx "sudo nginx -g 'daemon off;'"
tmux ls
