import asyncio
import logging
from datetime import datetime
from typing import Optional

log = logging.getLogger("aurora.trader")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

class Trader:
    def __init__(self, interval_seconds: float = 1.0):
        self.interval: float = float(interval_seconds)
        self._running: bool = False
        self._stop: Optional[asyncio.Event] = None

    async def tick_once(self) -> None:
        """
        Do ONE trading tick.
        TODO: wire in your real: datafeed -> strategies -> risk -> executor -> logging
        """
        # heartbeat so we can see it working
        log.info("tick @ %s", datetime.utcnow().isoformat() + "Z")
        await asyncio.sleep(0)  # yield to event loop

    async def tick_loop(self) -> None:
        """
        Forever loop that *awaits* tick_once() and sleeps between iterations.
        """
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

# ---- CLI entrypoint (tmux runs this module) ----
async def _amain() -> None:
    trader = Trader(interval_seconds=1.0)
    await trader.tick_loop()

def main() -> None:
    asyncio.run(_amain())

if __name__ == "__main__":
    main()
