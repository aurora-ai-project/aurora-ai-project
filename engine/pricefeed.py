from collections import deque
from typing import Deque, List, Callable

class PriceFeed:
    def __init__(self, maxlen: int = 500):
        self.buffer: Deque[float] = deque(maxlen=maxlen)
        self._subscribers: List[Callable[[float], None]] = []

    def push(self, price: float) -> int:
        self.buffer.append(float(price))
        for fn in self._subscribers:
            try:
                fn(float(price))
            except Exception:
                pass
        return len(self.buffer)

    def last(self, n: int = 1) -> list[float]:
        if n <= 0: return []
        return list(self.buffer)[-n:]

    def subscribe(self, fn: Callable[[float], None]) -> None:
        self._subscribers.append(fn)

feed = PriceFeed()
