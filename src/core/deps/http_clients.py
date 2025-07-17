from collections.abc import AsyncGenerator

from aiohttp import ClientSession
from dishka import Scope, provide
from httpx import AsyncClient

from src.core.deps.base import BaseProvider
from src.core.utils.http_clients import AIOHTTPClient, HTTPXClient, RESTClient, Session


class HTTPXProvider(BaseProvider):
    @provide(scope=Scope.REQUEST, provides=Session)
    async def get_session(self) -> AsyncGenerator[AsyncClient]:
        async with AsyncClient() as session:
            yield session

    client = provide(source=HTTPXClient, provides=RESTClient)


class AIOHTTPProvider(BaseProvider):
    @provide(scope=Scope.REQUEST, provides=Session)
    async def get_session(self) -> AsyncGenerator[ClientSession]:
        async with ClientSession() as session:
            yield session

    client = provide(source=AIOHTTPClient, provides=RESTClient)
