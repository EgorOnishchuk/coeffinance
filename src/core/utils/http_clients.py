from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from http import HTTPMethod
from typing import Any, Generic, Literal, TypeVar

from aiohttp import ClientConnectionError, ClientResponse, ClientResponseError, ClientSession, ClientTimeout
from httpx import AsyncClient, HTTPStatusError, RequestError, Response

from src.core.errors.exceptions import ExternalAPIError
from src.core.settings import ExternalAPISettings  # noqa: TC001

Session = AsyncClient | ClientSession
SessionT = TypeVar("SessionT", bound=Session)

type JSONScalar = str | int | float | bool | None
type JSON = dict[str, JSON | JSONScalar] | list[JSON | JSONScalar]

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
type JSONReturningMethod = Literal[HTTPMethod.GET, HTTPMethod.POST, HTTPMethod.PUT, HTTPMethod.PATCH, HTTPMethod.DELETE]


@dataclass(kw_only=True, slots=True, frozen=True)
class HTTPClient(ABC):
    _settings: ExternalAPISettings


class RESTClient(HTTPClient, Generic[SessionT]):
    @abstractmethod
    async def request_json(self, session: SessionT, url: str, method: JSONReturningMethod, **kwargs: Any) -> JSON:
        raise NotImplementedError


class HTTPXClient(RESTClient[AsyncClient]):
    async def _connect(self, session: AsyncClient, url: str, method: Method, **kwargs: Any) -> Response:
        try:
            response = await session.request(
                method,
                url,
                timeout=self._settings.timeout,
                **kwargs,
            )
        except RequestError as exc:
            raise ExternalAPIError from exc

        try:
            response.raise_for_status()
        except HTTPStatusError as exc:
            raise ExternalAPIError from exc

        return response

    async def request_json(self, session: AsyncClient, url: str, method: JSONReturningMethod, **kwargs: Any) -> JSON:
        return (await self._connect(session, url, method, **kwargs)).json()


class AIOHTTPClient(RESTClient[ClientSession]):
    async def _connect(self, session: ClientSession, url: str, method: Method, **kwargs: Any) -> ClientResponse:
        try:
            async with session.request(
                method,
                url,
                timeout=ClientTimeout(self._settings.timeout),
                **kwargs,
            ) as response:
                response.raise_for_status()

                return response
        except (ClientConnectionError, ClientResponseError) as exc:
            raise ExternalAPIError from exc

    async def request_json(self, session: ClientSession, url: str, method: JSONReturningMethod, **kwargs: Any) -> JSON:
        return await (await self._connect(session, url, method, **kwargs)).json()
