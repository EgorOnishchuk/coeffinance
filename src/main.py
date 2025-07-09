from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from src.dependencies import (
    get_compression_settings,
    get_cors_settings,
    get_docs_settings,
    get_trusted_hosts_settings,
    lifespan,
)
from src.errors import (
    DBConnError,
    db_conn_handler,
    external_api_handler,
    route_not_found_handler,
    unexpected_exception_handler,
    validation_handler,
)
from src.middlewares import VersionMiddleware
from src.persons.errors import ExternalAPIError
from src.persons.router import router as person_router
from src.reports.router import router as report_router

app: FastAPI = FastAPI(
    **get_docs_settings().model_dump(by_alias=True, exclude_none=True),
    lifespan=lifespan,
)

for middleware, settings in (
    (TrustedHostMiddleware, get_trusted_hosts_settings()),
    (CORSMiddleware, get_cors_settings()),
    (GZipMiddleware, get_compression_settings()),
):
    app.add_middleware(
        middleware,
        **settings.model_dump(by_alias=True, exclude_none=True),
    )

app.add_middleware(VersionMiddleware, version=get_docs_settings().version)

for exc, handler in (
    (RequestValidationError, validation_handler),
    (404, route_not_found_handler),
    (DBConnError, db_conn_handler),
    (ExternalAPIError, external_api_handler),
    (Exception, unexpected_exception_handler),
):
    app.add_exception_handler(exc, handler)

for router in person_router, report_router:
    app.include_router(router, prefix="/api")
