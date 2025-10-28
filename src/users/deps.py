from functools import lru_cache
from typing import Annotated

from dishka import Provider, provide
from fastapi import Depends
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    RedisStrategy,
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase

from src.core.asgi import Architecture, ExtendedRequest
from src.core.db.sessions import SQLAlchemySession
from src.core.deps.base import BaseProvider
from src.core.deps.db import Redis_
from src.core.settings import AuthSettings
from src.users.db.models import DBUserProtocol, SQLAlchemyUser
from src.users.service import UserManager
from src.users.utils.password_validators import (
    PasswordValidator,
    ZXCVBNValidator,
)


class ZXCVBNProvider(BaseProvider):
    validator = provide(
        source=ZXCVBNValidator,
        provides=PasswordValidator,
    )


class AuthProvider(BaseProvider):
    @provide
    def get_settings(self) -> AuthSettings:
        return AuthSettings.load()


@lru_cache
def get_fastapi_users() -> FastAPIUsers[DBUserProtocol, int]:
    """
    FastAPI Depends style is required here for integrating fastapi-users with
    Dishka Providers, as the lib is tightly coupled with the routing layer.
    This approach allows routers to be included in the app synchronously,
    since async deps are declared now but called later.
    """

    bearer = BearerTransport(
        tokenUrl=f"{Architecture.JSON_API}/{{version}}/users/auth/universal/login"
    )

    async def get_redis_strategy(
        request: ExtendedRequest,
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
        request: ExtendedRequest,
    ) -> SQLAlchemyUserDatabase[DBUserProtocol, int]:
        session = await request.state.dishka_container.get(SQLAlchemySession)

        return SQLAlchemyUserDatabase[DBUserProtocol, int](
            session=session,
            user_table=SQLAlchemyUser,
        )

    async def get_user_manager(
        request: ExtendedRequest,
        db: Annotated[
            SQLAlchemyUserDatabase[DBUserProtocol, int],
            Depends(get_sqlalchemy_db),
        ],
    ) -> UserManager:
        container = request.state.dishka_container

        return UserManager(
            user_db=db,
            settings=await container.get(AuthSettings),
            password_validator=await container.get(PasswordValidator),
        )

    return FastAPIUsers[DBUserProtocol, int](
        get_user_manager=get_user_manager,
        auth_backends=(universal_backend,),
    )


async def get_authenticated() -> DBUserProtocol:
    dep = get_fastapi_users().current_user(active=True, verified=True)
    return await dep()  # type: ignore[no-any-return] # pyright: ignore[reportReturnType]


def get_user_deps() -> tuple[Provider, ...]:
    return (
        ZXCVBNProvider(),
        AuthProvider(),
    )
