from collections.abc import AsyncGenerator

from dishka import Scope, provide
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.core.db.sessions import SQLAlchemySession
from src.core.deps.base import BaseProvider


class SQLAlchemyTestProvider(BaseProvider):
    @provide(scope=Scope.REQUEST, override=True)
    async def get_session(
        self, session_maker: async_sessionmaker[SQLAlchemySession]
    ) -> AsyncGenerator[SQLAlchemySession]:
        """
        To be able to test code that uses transactions itself. Also performs
        automatic rollback.
        """
        async with session_maker() as session, session.begin_nested():
            yield session
