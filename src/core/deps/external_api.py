from collections.abc import AsyncGenerator

from dishka import Scope, provide
from httpx import AsyncBaseTransport, AsyncHTTPTransport

from src.core.deps.base import BaseProvider
from src.core.external_api import (
    HTTPXSession,
    RESTSession,
)
from src.core.settings import ExternalAPISettings


class HTTPXProvider(BaseProvider):
    @provide
    def get_external_api_settings(self) -> ExternalAPISettings:
        return ExternalAPISettings.load()

    @provide(provides=AsyncBaseTransport)
    def get_transport_provider(
        self,
        settings: ExternalAPISettings,
    ) -> AsyncHTTPTransport:
        return AsyncHTTPTransport(retries=settings.retries)

    @provide(scope=Scope.REQUEST, provides=RESTSession)
    async def get_session(
        self,
        settings: ExternalAPISettings,
        transport: AsyncBaseTransport,
    ) -> AsyncGenerator[HTTPXSession]:
        async with HTTPXSession(
            _settings=settings,
            transport=transport,
        ) as session:
            yield session
