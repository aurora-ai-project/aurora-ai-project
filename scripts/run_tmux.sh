#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
SESSION=aurora_engine
tmux kill-session -t "$SESSION" 2>/dev/null || true
source venv/bin/activate
python3 -m pip install -r requirements.txt
AURORA_AUTOSTART=1 tmux new-session -d -s "$SESSION" "source venv/bin/activate && python3 main.py"
echo "Attached: tmux attach -t $SESSION"
