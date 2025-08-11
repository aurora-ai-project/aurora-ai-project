
    async def tick_loop(self):
        while True:
            await self.tick_once()
            await asyncio.sleep(self.interval)

