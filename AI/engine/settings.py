from pydantic import BaseModel
from pathlib import Path
import os
ROOT=Path(__file__).resolve().parents[1]
LOGS=ROOT/'logs'
MODELS=ROOT/'models'
STATE=LOGS/'state.json'
API_KEY=os.getenv('AURORA_API_KEY','dev-key')
SYMBOL=os.getenv('AURORA_SYMBOL','BTCUSDT')
INTERVAL_SEC=float(os.getenv('AURORA_TICK_SEC', '2'))
STAKE_FRACTION=float(os.getenv('AURORA_STAKE_FRACTION','0.1'))
MAX_PER_TRADE=float(os.getenv('AURORA_MAX_PER_TRADE','10'))
RESERVE_FRACTION=float(os.getenv('AURORA_RESERVE_FRACTION','0.5'))
SL_PCT=float(os.getenv('AURORA_SL_PCT','0.2'))
TP_PCT=float(os.getenv('AURORA_TP_PCT','0.3'))
MAX_POSITIONS=int(os.getenv('AURORA_MAX_POSITIONS','5'))
MAX_DD_PCT=float(os.getenv('AURORA_MAX_DD_PCT','0.15'))
START_EQUITY=float(os.getenv('AURORA_START_EQUITY','100'))
WS_TOPIC="aurora"
