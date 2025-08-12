import asyncio, logging, os
from datetime import datetime
from typing import Optional

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except Exception:
    pass

log = logging.getLogger("aurora.trader")
if not log.handlers:
    h = logging.StreamHandler()
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    h.setFormatter(fmt); log.addHandler(h); log.setLevel(logging.INFO)

class Trader:
    def __init__(self, interval_seconds: float = 1.0):
        self.interval = max(0.05, float(interval_seconds))
        self._running = False
        self._stop: Optional[asyncio.Event] = None

    async def tick_once(self) -> None:
        # TODO: datafeed -> strategies -> risk -> executor -> persist
        log.info("tick @ %s", datetime.utcnow().isoformat() + "Z")
        await asyncio.sleep(0)  # cooperative yield

    async def tick_loop(self) -> None:
        if self._running:
            return
        self._running, self._stop = True, asyncio.Event()
        try:
            while not self._stop.is_set():
                try:
                    await self.tick_once()
                except asyncio.CancelledError:
                    log.info("tick loop cancelled; shutting down cleanly")
                    break
                except Exception as e:
                    log.exception("tick error: %s", e)
                    await asyncio.sleep(0.25)  # brief backoff on failures
                await asyncio.sleep(self.interval)
        finally:
            self._running = False

    def stop(self) -> None:
        if self._stop is not None:
            self._stop.set()

async def _amain() -> None:
    t = Trader(interval_seconds=float(os.getenv("AURORA_TICK_INTERVAL", "1.0")))
    await t.tick_loop()

def main() -> None:
    try:
        asyncio.run(_amain())
    except (KeyboardInterrupt, asyncio.CancelledError):
        # graceful shutdown without traceback spam
        pass

if __name__ == "__main__":
    main()
