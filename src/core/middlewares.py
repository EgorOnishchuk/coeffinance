from uuid import UUID

from asgi_correlation_id import CorrelationIdMiddleware, correlation_id
from asgiref.typing import (
    ASGI3Application,
    ASGIReceiveCallable,
    ASGISendCallable,
    HTTPScope,
    Scope,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware import Middleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.requests import Request
from structlog.contextvars import bind_contextvars, clear_contextvars

from src.core.errors import CoreError
from src.core.settings import (
    NetworkSettings,
)
from src.core.utils.logging import IncomingHTTPRequestLog, logger


class LoggingMiddleware:
    """
    https://starlette.dev/middleware/#limitations
    """

    def __init__(self, app: ASGI3Application) -> None:
        self.app = app

    async def __call__(
        self, scope: Scope, receive: ASGIReceiveCallable, send: ASGISendCallable
    ) -> None:
        if not isinstance(scope, HTTPScope):
            await self.app(scope, receive, send)
            return

        clear_contextvars()
        request = Request(scope)
        bind_contextvars(
            **dict(
                IncomingHTTPRequestLog(
                    id=UUID(correlation_id.get()),
                    client_host=request.client.host,
                    client_port=request.client.port,
                    path=scope["path"],
                    version=scope["http_version"],
                    method=request.method,
                    path_params=request.path_params,
                    query_params=request.query_params,
                    body=await request.body(),
                    headers=request.headers,
                )
            )
        )

        try:
            await self.app(scope, receive, send)
        except Exception as exc:
            if isinstance(exc, CoreError):
                logger().log(
                    event=exc.type, level=exc.log_level, details=exc.details
                )
                raise

            logger().critical(
                event=type(exc).__name__,
            )
            raise


def core_middleware() -> tuple[Middleware, ...]:
    return (
        Middleware(
            CorrelationIdMiddleware,
        ),
        Middleware(
            LoggingMiddleware,
        ),
        Middleware(
            TrustedHostMiddleware, allowed_hosts=NetworkSettings().allowed_hosts
        ),
        Middleware(
            CORSMiddleware,
            allow_origins=NetworkSettings().allowed_origins,
            allow_methods=NetworkSettings().allowed_methods,
            allow_headers=NetworkSettings().allowed_headers,
            allow_credentials=NetworkSettings().are_credentials_allowed,
            allow_origin_regex=NetworkSettings().allowed_origin_regex,
            expose_headers=NetworkSettings().exposed_headers,
            max_age=NetworkSettings().cache_time,
        ),
        Middleware(
            GZipMiddleware,
            minimum_size=NetworkSettings.compression_min_size,
            compresslevel=NetworkSettings.compression_level,
        ),
    )
