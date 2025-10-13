from typing import Any

from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware import (
    _MiddlewareFactory,  # pyright: ignore[reportPrivateUsage]
)

from src.core.settings import (
    CompressionSettings,
    CORSSettings,
    TrustedHostsSettings,
)

#  A factory params and a settings dict must match. This cannot be
#  expressed through annotation, as the dict cannot be annotated via
#  P.kwargs.
type Middleware = tuple[_MiddlewareFactory[Any], dict[str, Any]]


def get_middleware_map() -> tuple[Middleware, ...]:
    return tuple(
        (  # type: ignore[misc] # A MyPy limitation when dealing with MiddlewareFactory, not confirmed by Pyright.
            middleware,
            settings.load().model_dump(
                by_alias=True,
                exclude_none=True,
            ),
        )
        for middleware, settings in (
            (TrustedHostMiddleware, TrustedHostsSettings),
            (CORSMiddleware, CORSSettings),
            (GZipMiddleware, CompressionSettings),
        )
    )
