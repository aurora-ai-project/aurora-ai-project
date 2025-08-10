#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && . ./.env && set +a
source venv/bin/activate
python main.py
