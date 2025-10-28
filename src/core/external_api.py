from abc import ABC, abstractmethod
from dataclasses import dataclass
from http import HTTPMethod
from typing import Any, Final, Literal, cast, override

from httpx import (
    AsyncClient,
    HTTPStatusError,
    RequestError,
    Response,
)

from src.core.errors import ExternalAPIConnError, ExternalRESTResponseError
from src.core.schemas import JSON
from src.core.settings import ExternalAPISettings

type Method = Literal[
    HTTPMethod.GET,
    HTTPMethod.POST,
    HTTPMethod.PUT,
    HTTPMethod.PATCH,
    HTTPMethod.DELETE,
    HTTPMethod.HEAD,
    HTTPMethod.OPTIONS,
    HTTPMethod.CONNECT,
    HTTPMethod.TRACE,
]
type JSONReturningMethod = Literal[
    HTTPMethod.GET,
    HTTPMethod.POST,
    HTTPMethod.PUT,
    HTTPMethod.PATCH,
    HTTPMethod.DELETE,
]


@dataclass(kw_only=True, slots=True)
class APISession(ABC):
    _settings: Final[ExternalAPISettings]  # type: ignore[misc] # A MyPy limitation when dealing with dataclasses with Final, not confirmed by Pyright: https://github.com/python/mypy/issues/5608.


class RESTSession(APISession):
    @abstractmethod
    async def request_json(
        self,
        *,
        url: str,
        method: JSONReturningMethod,
        **kwargs: Any,
    ) -> JSON:
        raise NotImplementedError


class HTTPXSession(AsyncClient, RESTSession):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            timeout=self._settings.timeout,
            **kwargs,
        )

    @override
    async def request(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Response:
        try:
            return await super().request(
                *args,
                **kwargs,
            )
        except RequestError as exc:
            raise ExternalAPIConnError(exc.args[0]) from exc

    @override
    async def request_json(
        self,
        *,
        url: str,
        method: JSONReturningMethod,
        **kwargs: Any,
    ) -> JSON:
        try:
            return cast(
                JSON,
                (
                    (await self.request(url=url, method=method, **kwargs))
                    .raise_for_status()
                    .json()
                ),
            )
        except HTTPStatusError as exc:
            raise ExternalRESTResponseError(
                exc.response.json(),
                code=exc.response.status_code,
            ) from exc
