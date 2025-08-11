"""
fastapi-users is hardwired with FastAPI Depends, so some providers create factories for the objects as dependencies
rather than the objects themselves to ensure correct integration of Dishka with Depends.
"""

from collections.abc import AsyncGenerator, Awaitable, Callable
from typing import Annotated, NewType

from dishka import provide
from fastapi import Depends
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, RedisStrategy
from fastapi_users.db import BaseUserDatabase
from fastapi_users.manager import UserManagerDependency
from fastapi_users.models import UP
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.core.deps.base import BaseProvider
from src.core.settings import AuthSettings
from src.core.utils.email_clients import EmailClient
from src.users.models import SQLAlchemyUser
from src.users.service import SQLAlchemyUserManager
from src.users.utils.utils import PasswordValidator, SecurePassLibValidator


class SecurePassLibValidatorProvider(BaseProvider):
    validator = provide(source=SecurePassLibValidator, provides=PasswordValidator, recursive=True)


MultiFrontend = NewType("MultiFrontend", AuthenticationBackend)


class BearerProvider(BaseProvider):
    @provide
    def get_transport(self) -> BearerTransport:
        return BearerTransport(tokenUrl="users/auth/login")


class RedisStrategyProvider(BaseProvider):
    @provide
    def get_strategy(self, redis: Redis) -> RedisStrategy:
        return RedisStrategy(redis, lifetime_seconds=3600)

    @provide
    def get_strategy_dep(self, strategy: RedisStrategy) -> Callable[[], AsyncGenerator[RedisStrategy]]:
        async def _strategy_dep() -> AsyncGenerator[RedisStrategy]:
            yield strategy

        return _strategy_dep


class MultiFrontendProvider(BaseProvider):
    @provide(provides=MultiFrontend)
    def get_auth(
        self, transport: BearerTransport, strategy_dep: Callable[[], AsyncGenerator[RedisStrategy]]
    ) -> AuthenticationBackend:
        return AuthenticationBackend(name="Multifrontend", transport=transport, get_strategy=strategy_dep)


class UserManagerSQLAlchemyProvider(BaseProvider):
    @provide(provides=type[UP])
    def get_model(self) -> type[SQLAlchemyUser]:
        return SQLAlchemyUser

    @provide
    def get_session_dep(
        self, session_maker: async_sessionmaker[AsyncSession]
    ) -> Callable[[], AsyncGenerator[AsyncSession]]:
        async def _session_dep() -> AsyncGenerator[AsyncSession]:
            async with session_maker() as session:
                try:
                    yield session
                    await session.commit()
                except:
                    await session.rollback()
                    raise
                finally:
                    await session.close()

        return _session_dep

    @provide(provides=Callable[[AsyncSession], Awaitable[BaseUserDatabase]])
    def get_db_dep(
        self, session_dep: Callable[[], AsyncGenerator[AsyncSession]], model: type[UP]
    ) -> Callable[[AsyncSession], Awaitable[SQLAlchemyUserDatabase]]:
        async def _db_dep(session: Annotated[AsyncSession, Depends(session_dep)]) -> SQLAlchemyUserDatabase:
            return SQLAlchemyUserDatabase(session=session, user_table=model)

        return _db_dep

    @provide(provides=UserManagerDependency)
    def get_manager_dep(
        self,
        db_dep: Callable[[AsyncSession], Awaitable[BaseUserDatabase]],
        settings: AuthSettings,
        client: EmailClient,
        validator: PasswordValidator,
    ) -> Callable[[BaseUserDatabase], Awaitable[SQLAlchemyUserManager]]:
        async def _manager_dep(db: Annotated[BaseUserDatabase, Depends(db_dep)]) -> SQLAlchemyUserManager:
            return SQLAlchemyUserManager(
                user_db=db, settings=settings, email_client=client, password_validator=validator
            )

        return _manager_dep


class FastAPIUsersProvider(BaseProvider):
    @provide
    def get_fastapi_users(
        self,
        manager: UserManagerDependency,
        multi_frontend: MultiFrontend,
    ) -> FastAPIUsers:
        return FastAPIUsers(get_user_manager=manager, auth_backends=[multi_frontend])


def get_user_deps() -> tuple[BaseProvider, ...]:
    return (
        SecurePassLibValidatorProvider(),
        BearerProvider(),
        RedisStrategyProvider(),
        MultiFrontendProvider(),
        UserManagerSQLAlchemyProvider(),
        FastAPIUsersProvider(),
    )
