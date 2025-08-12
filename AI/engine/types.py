from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, Any, List
from datetime import datetime
class Bar(BaseModel):
    ts: datetime
    symbol: str
    price: float
class StrategyVote(BaseModel):
    name: str
    bias: float = Field(ge=-1.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    note: str = ""
    features: Optional[Dict[str, float]] = None
class Decision(BaseModel):
    action: Literal['BUY','SELL','HOLD']
    confidence: float
    reason: str
    votes: List[StrategyVote]
class Position(BaseModel):
    symbol: str; qty: float; entry: float; stake: float; ts: datetime
class Fill(BaseModel):
    symbol: str; side: Literal['BUY','SELL']; qty: float; price: float; ts: datetime
class State(BaseModel):
    equity: float; cash: float; positions: List[Position]; peak_equity: float; halted: bool
