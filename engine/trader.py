import asyncio
import logging
from datetime import datetime
from typing import Optional

log = logging.getLogger("aurora.trader")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

class Trader:
    def __init__(self, interval_seconds: float = 1.0):
        self.interval = float(interval_seconds)
        self._running = False
        self._stop: Optional[asyncio.Event] = None

    async def tick_once(self) -> None:
        log.info("tick @ %s", datetime.utcnow().isoformat() + "Z")
        await asyncio.sleep(0)

    async def tick_loop(self) -> None:
        if self._running:
            return
        self._running = True
        self._stop = asyncio.Event()
        try:
            while not self._stop.is_set():
                await self.tick_once()
                await asyncio.sleep(self.interval)
        finally:
            self._running = False

    def stop(self) -> None:
        if self._stop is not None:
            self._stop.set()

async def _amain() -> None:
    trader = Trader(interval_seconds=1.0)
    await trader.tick_loop()

def main() -> None:
    asyncio.run(_amain())

if __name__ == "__main__":
    main()
