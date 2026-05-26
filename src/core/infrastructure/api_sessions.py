from __future__ import annotations

from datetime import timedelta
from http import HTTPStatus
from json import JSONDecodeError
from random import uniform
from typing import Any, Final, Literal, override

from httpx import (
    URL,
    USE_CLIENT_DEFAULT,
    AsyncClient,
    HTTPStatusError,
    RequestError,
    Response,
)
from httpx._client import UseClientDefault
from httpx._types import (
    HeaderTypes,
    QueryParamTypes,
    TimeoutTypes,
)
from limits import RateLimitItemPerSecond
from limits.aio.storage import Storage
from limits.aio.strategies import (
    RateLimitItem,
)
from starlette import status
from tenacity import RetryCallState

from src.core.errors import ExternalAPIConnError
from src.core.utils.limits import FixedWindowLimiter, Limiter
from src.core.utils.logging import (
    IncomingHTTPResponseLog,
    OutgoingHTTPRequestLog,
    RESTLog,
    bind,
)
from src.core.utils.retries import backoff
from src.core.utils.typing import downcast
from src.core.validators import JSON

type HTTPMethod = Literal[
    "CONNECT",
    "DELETE",
    "GET",
    "HEAD",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
    "TRACE",
]

class Sessionmaker(AsyncClient):
    def __init__(
        self,
        *,
        rate_limits_db: Storage,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._rate_limits_db: Final = rate_limits_db

    @override
    async def request(
        self,
        url: URL | str,
        method: str,
        *,
        json: Any | None = None,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
        timeout: TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT,
        window: RateLimitItem = RateLimitItemPerSecond(1),
        limit_strategy: type[Limiter] = FixedWindowLimiter,
        limit_id: str | None = None,
        **kwargs: Any,
    ) -> ResponseExtended:
        if isinstance(url, str):
            url = URL(url)

        if limit_id is None:
            limit_id = f"{url.host}{url.path}"
        limiter = limit_strategy(self._rate_limits_db)

        request_log = OutgoingHTTPRequestLog.from_url(
            url,
            method=method, headers=headers, params=params,
        )

        try:
            await limiter.wait_until_allowed(
                window=window,
                id_=limit_id,
            )

            response = await super().request(
                method,
                url,
                json=json,
                params=params,
                headers=headers,
                timeout=timeout,
                **kwargs,
            )
        except RequestError as exc:
            raise ExternalAPIConnError from exc

        response = downcast(
            source=response,
            target=ResponseExtended,
        )

        try:
            return response.raise_for_status()
        except HTTPStatusError as exc:
            bind(
                request_log,
                IncomingHTTPResponseLog(
                    code=exc.response.status_code,
                    headers=exc.response.headers,
                ),
            )

            if exc.response
                raise TempServerError from exc

            raise

    async def fetch_resource(
        self,
        url: URL,
        method: HTTPMethod,
        *,
        body: JSON | None = None,
        query_params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
        timeout: timedelta = timedelta(seconds=10),
        in_parallel: int = 100,
        window: RateLimitItem = RateLimitItemPerSecond(1),
        limit_strategy: type[Limiter] = FixedWindowLimiter,
        limit_id: str | None = None,
    ) -> JSON | None:
        log = RESTLog(
            request_body=body,
        )

        try:
            response = await self.request(
                url,
                method,
                json=body,
                params=query_params,
                headers=headers,
                timeout=timeout.total_seconds(),
                in_parallel=in_parallel,
                window=window,
                limit_strategy=limit_strategy,
                limit_id=limit_id,
            )
        except HTTPStatusError as status_exc:
            try:
                json = self._json_or_none(status_exc.response)
            except JSONDecodeError as json_exc:
                bind(log)
                raise json_exc from status_exc

            log.response_body = json
            bind(log)

            raise

        try:
            return response.json_or_none()
        except JSONDecodeError:
            bind(log)
            raise

    @staticmethod
    def wait_retry_after(retry_state: RetryCallState) -> float:
        exc = retry_state.outcome.exception()
        if all((
            isinstance(exc, TempServerError),
            exc.retry_after is not None,
        )):
            jitter = uniform(0, exc.retry_after * 0.1)
            return exc.retry_after + jitter

        return backoff()(retry_state)


class ResponseExtended(Response):
    def is_temp_server_error(self) -> bool:
        return self.status_code in (
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_502_BAD_GATEWAY,
            status.HTTP_503_SERVICE_UNAVAILABLE,
            status.HTTP_504_GATEWAY_TIMEOUT,
        )

    def json_or_none(self) -> JSON | None:
        return self.json() if self.content else None


class HTTPStatusErrorExtended(HTTPStatusError):
    ...


class TempServerError(HTTPStatusErrorExtended):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.retry_after: Final = self.response.headers.get("Retry-After")
