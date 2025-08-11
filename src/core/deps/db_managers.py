from collections.abc import AsyncGenerator

import redis.asyncio
from dishka import Scope, from_context, provide
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from src.core.deps.base import BaseProvider
from src.core.settings import CacheCredentials, DBCredentials, DBPoolSettings
from src.core.utils.db_managers import DBManager, SQLAlchemyCompatible, SQLAlchemyDBManager


class SQLAlchemyProvider(BaseProvider):
    @provide
    def get_engine(self, credentials: DBCredentials, settings: DBPoolSettings) -> AsyncEngine:
        return create_async_engine(credentials.dsn, **settings.model_dump(by_alias=True))

    @provide
    def get_session_maker(self, engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(engine, expire_on_commit=False)

    model = from_context(provides=type[SQLAlchemyCompatible])

    manager = provide(source=SQLAlchemyDBManager, provides=DBManager)

    @provide(scope=Scope.REQUEST)
    async def get_session(self, session_maker: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession]:
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
    def get_redis(self, settings: CacheCredentials) -> Redis:
        return redis.asyncio.from_url(settings.dsn)
