
from dishka import provide
from httpx import AsyncBaseTransport, AsyncHTTPTransport
from limits.aio.storage import RedisStorage, Storage

from src.core.deps.base import CoreProvider
from src.core.infrastructure.api_sessions import (
    Sessionmaker,
)
from src.core.settings import IMDBCredentials


class RedisLimitsProvider(CoreProvider):
    @provide(provides=Storage)
    def db(self) -> RedisStorage:
        return RedisStorage(
            f"async+{IMDBCredentials}", implementation="redispy",
        )


class HTTPXProvider(CoreProvider):
    transport = provide(AsyncHTTPTransport, provides=AsyncBaseTransport)

    @provide
    async def sessionmaker(
        self,
        transport: AsyncBaseTransport,
        rate_limits_db: Storage,
    ) -> Sessionmaker:
        return Sessionmaker(
            transport=transport,
            rate_limits_db=rate_limits_db,
        )
