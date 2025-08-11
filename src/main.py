from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from src.users.deps import get_user_deps

if TYPE_CHECKING:
    from dishka import AsyncContainer
from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from src.core.deps.base import SettingsProvider, UvicornLoggerProvider
from src.core.deps.db_managers import RedisProvider, SQLAlchemyProvider
from src.core.deps.email_clients import AIOSMTPLibProvider
from src.core.deps.http_clients import HTTPXProvider
from src.core.errors import (
    DBError,
    EmailConnError,
    ExternalAPIError,
    db_conn_handler,
    email_conn_handler,
    external_api_handler,
    not_found_handler,
    unauthenticated_handler,
    unauthorized_handler,
    unexpected_exception_handler,
    validation_handler,
)
from src.core.middlewares import VersionMiddleware
from src.core.models import SQLAlchemyModel
from src.core.settings import CompressionSettings, CORSSettings, DocsSettings, TrustedHostsSettings
from src.core.utils.db_managers import SQLAlchemyCompatible
from src.users.errors import (
    AlreadyExistsError,
    AlreadyVerifiedError,
    AuthenticationError,
    PasswordResetError,
    UnverifiedError,
    VerificationError,
    WeakPasswordError,
    already_exists_handler,
    already_verified_handler,
    authentication_handler,
    password_reset_handler,
    unverified_handler,
    verification_handler,
    weak_password_handler,
)
from src.users.routes import UserRouterManager

container = make_async_container(
    SettingsProvider(),
    UvicornLoggerProvider(),
    SQLAlchemyProvider(),
    RedisProvider(),
    AIOSMTPLibProvider(),
    HTTPXProvider(),
    *get_user_deps(),
    context={
        type[SQLAlchemyCompatible]: SQLAlchemyModel,
    },
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    web_container: AsyncContainer = app.state.dishka_container

    for manager in (UserRouterManager,):
        await manager(app=app).attach()

    yield

    await web_container.close()


def main() -> FastAPI:
    docs = DocsSettings()

    app = FastAPI(
        **docs.model_dump(by_alias=True, exclude_none=True),
        lifespan=lifespan,
    )
    setup_dishka(container, app)

    for middleware, settings in (
        (TrustedHostMiddleware, TrustedHostsSettings),
        (CORSMiddleware, CORSSettings),
        (GZipMiddleware, CompressionSettings),
    ):
        app.add_middleware(
            middleware,
            **settings().model_dump(by_alias=True, exclude_none=True),
        )
    app.add_middleware(VersionMiddleware, version=docs.version)

    for exc, handler in (
        (RequestValidationError, validation_handler),
        (DBError, db_conn_handler),
        (EmailConnError, email_conn_handler),
        (ExternalAPIError, external_api_handler),
        (401, unauthenticated_handler),
        (403, unauthorized_handler),
        (404, not_found_handler),
        (Exception, unexpected_exception_handler),
        (WeakPasswordError, weak_password_handler),
        (AlreadyExistsError, already_exists_handler),
        (AuthenticationError, authentication_handler),
        (UnverifiedError, unverified_handler),
        (VerificationError, verification_handler),
        (AlreadyVerifiedError, already_verified_handler),
        (PasswordResetError, password_reset_handler),
    ):
        app.add_exception_handler(exc, handler)  # type: ignore[arg-type]

    return app
