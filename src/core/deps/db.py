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

from src.core.db.sessions import SQLAlchemySession
from src.core.deps.base import BaseProvider
from src.core.settings import (
    DBCredentials,
    DBSettings,
    RedisCredentials,
)

# Generic in stubs, but not in runtime: https://github.com/python/typeshed/issues/8242.
if TYPE_CHECKING:
    type Redis_ = Redis[str]
else:
    type Redis_ = Redis


class SQLAlchemyProvider(BaseProvider):
    @provide
    def get_db_credentials(self) -> DBCredentials:
        return DBCredentials.load()

    @provide
    def get_db_settings(self) -> DBSettings:
        return DBSettings.load()

    @provide
    def get_engine(
        self, credentials: DBCredentials, settings: DBSettings
    ) -> AsyncEngine:
        return create_async_engine(
            credentials.dsn,
            pool_size=settings.size,
            pool_timeout=settings.timeout,
            max_overflow=settings.overflow,
            pool_pre_ping=True,
        )

    @provide
    def get_session_maker(
        self,
        engine: AsyncEngine,
        settings: DBSettings,
    ) -> async_sessionmaker[SQLAlchemySession]:
        return async_sessionmaker(
            engine,
            class_=SQLAlchemySession,
            expire_on_commit=False,
            settings=settings,
        )

    @provide(scope=Scope.REQUEST)
    async def get_session(
        self, session_maker: async_sessionmaker[SQLAlchemySession]
    ) -> AsyncGenerator[SQLAlchemySession]:
        async with session_maker() as session:
            try:
                yield session
                await session.commit()
            except:
                await session.rollback()
                raise
            finally:
                await session.close()


class RedisProvider(BaseProvider):
    @provide
    def get_cache_credentials(self) -> RedisCredentials:
        return RedisCredentials.load()

    @provide
    def get_redis(self, settings: RedisCredentials) -> Redis_:
        return redis.asyncio.from_url(settings.dsn)
