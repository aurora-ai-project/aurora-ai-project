from typing import List
from .types import StrategyVote, Decision
def combine_votes(votes: List[StrategyVote]) -> Decision:
    if not votes:
        return Decision(action='HOLD', confidence=0.0, reason='no-votes', votes=[])
    num = sum(v.bias * max(v.confidence,1e-6) for v in votes)
    den = sum(max(v.confidence,1e-6) for v in votes)
    score = num / den if den else 0.0
    conf = min(sum(v.confidence for v in votes)/max(len(votes),1), 1.0)
    if score > 0.15: act = 'BUY'
    elif score < -0.15: act = 'SELL'
    else: act = 'HOLD'
    reason = f"score={score:.3f} conf={conf:.2f}"
    return Decision(action=act, confidence=conf, reason=reason, votes=votes)
