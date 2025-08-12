#!/usr/bin/env bash
set -e
SESSION=aurora
tmux has-session -t "$SESSION" 2>/dev/null && tmux kill-session -t "$SESSION" || true
tmux new-session -d -s "$SESSION" -n api "cd $(dirname $0)/.. && AURORA_API_KEY=\${AURORA_API_KEY:-dev-key} python3 main.py"
tmux new-window -t "$SESSION":2 -n trader "cd $(dirname $0)/.. && AURORA_API_KEY=\${AURORA_API_KEY:-dev-key} python3 -c 'from engine.trader import main; import asyncio; asyncio.run(main())'"
tmux new-window -t "$SESSION":3 -n logs "cd $(dirname $0)/../../logs && tail -f trade_log.csv || sleep infinity"
tmux select-window -t "$SESSION":1
echo "tmux session '$SESSION' started: windows [api, trader, logs]"
