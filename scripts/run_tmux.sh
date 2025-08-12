#!/usr/bin/env bash
set -e
SESSION=aurora
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

tmux has-session -t "$SESSION" 2>/dev/null && tmux kill-session -t "$SESSION" || true

tmux new-session -d -s "$SESSION" -n api    "cd \"$ROOT\" && AURORA_API_KEY=\${AURORA_API_KEY:-dev-key} python3 main.py"
tmux new-window  -t "$SESSION" -n trader    "cd \"$ROOT\" && AURORA_API_KEY=\${AURORA_API_KEY:-dev-key} python3 -c 'from engine.trader import main; import asyncio; asyncio.run(main())'"
tmux new-window  -t "$SESSION" -n logs      "cd \"$ROOT/logs\" && touch trade_log.csv && tail -f trade_log.csv || sleep infinity"

tmux select-window -t "$SESSION:api"
echo "tmux session '$SESSION' started: [api, trader, logs]"
