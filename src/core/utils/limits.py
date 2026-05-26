from abc import ABC
from asyncio import sleep
from time import time as now

from limits import RateLimitItem
from limits.aio.strategies import FixedWindowRateLimiter, RateLimiter


class Limiter(RateLimiter, ABC):
    async def wait_until_allowed(
        self,
        *,
        window: RateLimitItem,
        id_: str,
    ) -> None:
        while not await self.hit(window, id_):
            await self._wait_for_reset(window=window, id_=id_)

    async def _wait_for_reset(
        self,
        *,
        window: RateLimitItem,
        id_: str,
    ) -> None:
        stats = await self.get_window_stats(window, id_)

        await sleep(stats.reset_time - now())


class FixedWindowLimiter(FixedWindowRateLimiter, Limiter):
    pass
