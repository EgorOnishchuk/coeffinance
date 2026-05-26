from collections.abc import AsyncGenerator, Awaitable, Callable
from functools import lru_cache
from typing import Annotated, cast

from dishka import Provider, provide
from fastapi import Depends
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    RedisStrategy,
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from structlog.contextvars import bound_contextvars

from src.core.asgi import APIArchitecture, TypedRequest
from src.core.deps.base import CoreProvider
from src.core.deps.db_sessions import Redis_
from src.core.infrastructure.db_sessions import Session
from src.core.settings import VerificationSettings
from src.users.infrastructure.db_models import DBUserProtocol, SQLAlchemyUser
from src.users.services import UserManager
from src.users.utils.password_validators import (
    PasswordValidator,
    ZXCVBNValidator,
)


class ZXCVBNProvider(CoreProvider):
    validator = provide(
        source=ZXCVBNValidator,
        provides=PasswordValidator,
    )


class AuthProvider(CoreProvider):
    @provide
    def get_settings(self) -> VerificationSettings:
        return VerificationSettings.load()


@lru_cache
def get_fastapi_users() -> FastAPIUsers[DBUserProtocol, int]:
    """
    FastAPI Depends style is required here for integrating fastapi-users with
    Dishka Providers, as the lib is tightly coupled with the routing layer.
    This approach allows routers to be included in the app synchronously,
    since async deps are declared now but called later.
    """

    bearer = BearerTransport(
        tokenUrl=f"{APIArchitecture.REST}/{{version}}/users/auth/universal/login"
    )

    async def get_redis_strategy(
        request: TypedRequest,
    ) -> RedisStrategy[DBUserProtocol, int]:
        redis_ = await request.state.dishka_container.get(Redis_)

        return RedisStrategy[DBUserProtocol, int](redis_, lifetime_seconds=3600)

    # «Universal» here means the ability to be used equally effectively with
    # different frontends thanks to the platform-independent Bearer and
    # lightweight Redis.
    universal_backend = AuthenticationBackend[DBUserProtocol, int](
        name="universal",
        transport=bearer,
        get_strategy=get_redis_strategy,
    )

    async def get_sqlalchemy_db(
        request: TypedRequest,
    ) -> SQLAlchemyUserDatabase[DBUserProtocol, int]:
        session = await request.state.dishka_container.get(Session)

        return SQLAlchemyUserDatabase[DBUserProtocol, int](
            session=session,
            user_table=SQLAlchemyUser,
        )

    async def get_user_manager(
        request: TypedRequest,
        db: Annotated[
            SQLAlchemyUserDatabase[DBUserProtocol, int],
            Depends(get_sqlalchemy_db),
        ],
    ) -> UserManager:
        container = request.state.dishka_container

        return UserManager(
            user_db=db,
            settings=await container.get(VerificationSettings),
            password_validator=await container.get(PasswordValidator),
        )

    return FastAPIUsers[DBUserProtocol, int](
        get_user_manager=get_user_manager,
        auth_backends=(universal_backend,),
    )


async def get_authenticated() -> AsyncGenerator[DBUserProtocol]:
    # If optional=False (default) result cannot be None.
    dep = cast(
        Callable[..., Awaitable[DBUserProtocol]],
        get_fastapi_users().current_user(active=True, verified=True),
    )
    user = await dep()

    with bound_contextvars(nickname=user.nickname):
        yield user


def get_user_deps() -> tuple[Provider, ...]:
    return (
        ZXCVBNProvider(),
        AuthProvider(),
    )
