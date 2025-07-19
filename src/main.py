from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dishka import AsyncContainer

from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from src.analytics.routes import router as analytics_router
from src.companies.routes import router as companies_router
from src.core.deps.containers import container
from src.core.errors.exceptions import DBConnError, ExternalAPIError
from src.core.errors.handlers import (
    db_conn_handler,
    external_api_handler,
    route_not_found_handler,
    unexpected_exception_handler,
    validation_handler,
)
from src.core.middlewares import VersionMiddleware
from src.core.settings import CompressionSettings, CORSSettings, DocsSettings, TrustedHostsSettings
from src.users.routes import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    web_container: AsyncContainer = app.state.dishka_container

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
        (404, route_not_found_handler),
        (DBConnError, db_conn_handler),
        (ExternalAPIError, external_api_handler),
        (Exception, unexpected_exception_handler),
    ):
        app.add_exception_handler(exc, handler)  # type: ignore[arg-type]

    for router in (
        users_router,
        companies_router,
        analytics_router,
    ):
        app.include_router(router, prefix="/api")

    return app
