from pathlib import Path
import csv
from typing import List, Dict, Any

TRADE_LOG = Path("logs/trade_log.csv")

def tail_trades(n: int = 50) -> List[Dict[str, Any]]:
    if not TRADE_LOG.exists():
        return []
    rows = list(csv.DictReader(TRADE_LOG.open()))
    return rows[-n:]
