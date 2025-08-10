import json, random
from pathlib import Path
import numpy as np

MODEL = Path("models/ai_linear.json")
ACTIONS = ["HOLD","BUY","SELL"]
_LAST = {"reward": 0.0, "conf": 0.0, "action": "HOLD"}

def _features(history_prices, pos_qty, cash, price, k=20):
    hp = history_prices[-k:] if len(history_prices) >= k else [price]*(k-len(history_prices)) + list(history_prices)
    hp = np.array(hp, dtype=float)
    rets = np.diff(hp, prepend=hp[0])
    if hp[-1] != 0:
        rets = rets / (abs(hp[-1]) + 1e-9)
    pos_flag = np.array([1.0 if pos_qty>0 else 0.0, cash/(cash + pos_qty*price + 1e-9)], dtype=float)
    return np.concatenate([rets[-k:], pos_flag])

class LinearQLearner:
    def __init__(self, k=20, alpha=0.01, gamma=0.95, eps=0.1, stake=0.10):
        self.k, self.alpha, self.gamma, self.eps, self.stake = k, alpha, gamma, eps, stake
        self.W = np.zeros((3, k+2), dtype=float)

    def qvals(self, x): return self.W @ x
    def act(self, x): return random.randrange(3) if random.random()<self.eps else int(np.argmax(self.qvals(x)))
    def td_update(self, x, a, r, x2, terminal=False):
        q = self.qvals(x); target = r if terminal else r + self.gamma*np.max(self.qvals(x2))
        self.W[a] += self.alpha * (target - q[a]) * x
    def save(self): MODEL.parent.mkdir(parents=True, exist_ok=True); json.dump(
        {"k":self.k,"alpha":self.alpha,"gamma":self.gamma,"eps":self.eps,"stake":self.stake,"W":self.W.tolist()}, MODEL.open("w"))
    def load(self):
        if MODEL.exists():
            d = json.load(MODEL.open()); self.k=d.get("k",self.k); self.alpha=d.get("alpha",self.alpha)
            self.gamma=d.get("gamma",self.gamma); self.eps=d.get("eps",self.eps); self.stake=d.get("stake",self.stake)
            self.W = np.array(d["W"], dtype=float)

AGENT = LinearQLearner()
def set_eps(e): AGENT.eps = float(e)
def set_stake(s): AGENT.stake = float(s)
def save(): AGENT.save()
def load(): AGENT.load()

def step(history, pos_qty, cash, price, reward):
    x = _features(history, pos_qty, cash, price, AGENT.k)
    a = AGENT.act(x)
    AGENT.td_update(x, a, reward, x, terminal=False)
    conf = float(np.clip(np.max(AGENT.qvals(x)), 0, 10))/10.0
    action = ACTIONS[a]
    stake = max(0.02, min(0.25, AGENT.stake * (0.5 + 0.5*conf)))
    _LAST.update({"reward": float(reward), "conf": float(conf), "action": action})
    return {"action": action, "stake": stake, "conf": round(conf,3)}

def status():
    return {
        "alpha": AGENT.alpha, "gamma": AGENT.gamma, "eps": AGENT.eps, "stake": AGENT.stake,
        "last": dict(_LAST), "weights_shape": list(AGENT.W.shape)
    }
