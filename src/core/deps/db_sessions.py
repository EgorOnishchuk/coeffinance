from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

import redis.asyncio
from dishka import Scope, provide
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

from src.core.deps.base import CoreProvider
from src.core.infrastructure.db_sessions import Session
from src.core.settings import (
    ODDBCredentials,
    ODDBSettings,
    RedisCredentials,
)

# Generic in stubs, but not in runtime: https://github.com/python/typeshed/issues/8242.
if TYPE_CHECKING:
    type Redis_ = Redis[str]
else:
    type Redis_ = Redis


class SQLAlchemyProvider(CoreProvider):
    @provide
    def engine(
        self,
    ) -> AsyncEngine:
        return create_async_engine(
            str(ODDBCredentials()),
            pool_size=ODDBSettings().pool_size,
            pool_timeout=ODDBSettings().timeout,
            max_overflow=ODDBSettings().pool_overflow,
            pool_pre_ping=True,
        )

    @provide
    def sessionmaker(
        self,
        engine: AsyncEngine,
    ) -> async_sessionmaker[Session]:
        return async_sessionmaker(
            engine,
            class_=Session,
            expire_on_commit=False,
        )

    @provide(scope=Scope.REQUEST)
    async def get_session(
        self, sessionmaker: async_sessionmaker[Session]
    ) -> AsyncGenerator[Session]:
        async with sessionmaker() as session:
            try:
                yield session
                await session.commit()
            except:
                await session.rollback()
                raise
            finally:
                await session.close()


class RedisProvider(CoreProvider):
    @provide
    def get_client(self) -> Redis_:
        return redis.asyncio.from_url(RedisCredentials().dsn)
