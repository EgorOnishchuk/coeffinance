from abc import ABC
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from asyncpg.pool import PoolConnectionProxy
from httpx import ASGITransport, AsyncClient

from src.db.db_manager import AsyncpgManager
from src.dependencies import get_api_settings
from src.main import app
from src.persons.dependencies import get_fakerapi_client
from tests.utils.clients import MockClient


class TestAPI(ABC):
    route: str
    timeout: float = get_api_settings().timeout

    @pytest.fixture(scope="session", autouse=True)
    def mock(self) -> None:
        app.dependency_overrides[get_fakerapi_client] = lambda: MockClient()

    @pytest_asyncio.fixture()
    async def session(self) -> AsyncGenerator[AsyncClient]:
        async with (
            LifespanManager(app) as manager,
            AsyncClient(
                transport=ASGITransport(
                    app=manager.app,
                    client=(get_api_settings().host, get_api_settings().port),
                ),
                base_url="http://test",
            ) as session,
        ):
            yield session


class TestUnit(ABC):
    service_cls: type[Any]
    dal_cls: type[Any]

    @pytest_asyncio.fixture
    async def conn_(
        self,
        db_manager: AsyncpgManager,
    ) -> AsyncGenerator[PoolConnectionProxy]:
        async with db_manager.get_conn() as conn:
            yield conn
