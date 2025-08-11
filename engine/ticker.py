import os, asyncio, time
from typing import Any, Dict, Optional

class Ticker:
    def __init__(self, interval: float = 1.0):
        self.interval = float(interval)
        self._task: Optional[asyncio.Task] = None
        self._stop = asyncio.Event()
        self.last_tick: Optional[float] = None
        self.count: int = 0

    async def tick_once(self) -> Dict[str, Any]:
        self.last_tick = time.time()
        self.count += 1
        await asyncio.sleep(0)
        return {"ts": self.last_tick, "count": self.count}

    async def _loop(self) -> None:
        self._stop.clear()
        try:
            while not self._stop.is_set():
                await self.tick_once()
                await asyncio.sleep(self.interval)
        finally:
            self._task = None

    def start(self) -> bool:
        if self._task and not self._task.done():
            return False
        self._task = asyncio.create_task(self._loop())
        return True

    def stop(self) -> bool:
        self._stop.set()
        return True

ticker = Ticker(float(os.getenv("AURORA_TICK_INTERVAL", "1.0")))
