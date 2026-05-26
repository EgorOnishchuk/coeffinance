from collections.abc import AsyncGenerator

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.core.deps.base import CoreProvider
from src.core.infrastructure.db_sessions import Session
from tests.test_companies.deps import CompanyServiceMockProvider


class SQLAlchemyTestProvider(CoreProvider):
    @provide(scope=Scope.REQUEST, override=True)
    async def get_session(
        self, session_maker: async_sessionmaker[Session]
    ) -> AsyncGenerator[Session]:
        """
        To be able to test code that uses transactions itself. Also performs
        automatic rollback.
        """
        async with session_maker() as session, session.begin_nested():
            yield session


def get_test_deps() -> tuple[Provider, ...]:
    return (
        *get_prod_deps(),
        SQLAlchemyTestProvider(),
        CompanyServiceMockProvider(),
    )
