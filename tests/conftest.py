import os
from collections.abc import AsyncGenerator, Generator, Sequence
from typing import (
    Any,
    cast,
)

import pytest
import pytest_asyncio
from _pytest.fixtures import FixtureRequest
from alembic import command
from alembic.config import Config
from asgi_lifespan import LifespanManager
from cadwyn import Version, VersionBundle
from dishka import (
    STRICT_VALIDATION,
    AsyncContainer,
    Provider,
    make_async_container,
)
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Select
from starlette.types import ASGIApp
from testcontainers.postgres import (  # pyright: ignore[reportMissingTypeStubs] # The lib is de facto typed: https://github.com/testcontainers/testcontainers-python/issues/305.
    PostgresContainer,
)

from src.companies.routes import get_company_router
from src.core.asgi import ExtendedFastAPI
from src.core.db.models import SQLAlchemyPKModel
from src.core.db.sessions import SQLAlchemySession
from src.core.errors import get_handling_map
from src.core.middlewares import get_middleware_map
from src.core.settings import DocsSettings, ExternalAPISettings
from src.core.utils.paginators import FastAPIPagination
from src.main import get_prod_deps
from src.users.db.models import SQLAlchemyUser
from src.users.deps import get_authenticated
from src.users.errors import get_user_handling_map
from src.users.routes import get_user_router
from tests.deps import SQLAlchemyTestProvider
from tests.factories import (
    ExtendedSQLAlchemyFactory,
    SQLAlchemyPersistence,
)
from tests.test_companies.deps import CompanyServiceMockProvider
from tests.test_users.factories import SQLAlchemyUserFactory


def get_test_deps() -> tuple[Provider, ...]:
    return (
        *get_prod_deps(),
        SQLAlchemyTestProvider(),
        CompanyServiceMockProvider(),
    )


@pytest_asyncio.fixture
async def container() -> AsyncGenerator[AsyncContainer]:
    container = make_async_container(
        *get_test_deps(),
        validation_settings=STRICT_VALIDATION,
    )

    yield container

    await container.close()


@pytest.fixture
def overridden_container(
    request: FixtureRequest, container: AsyncContainer
) -> AsyncContainer:
    """
    Since it is impossible to directly override a provider in the container, it
    is necessary to create a new container by rebuilding the dependency graph.
    """
    providers = cast(
        Sequence[Provider],
        request.param,
    )

    return make_async_container(
        *get_test_deps(),
        *providers,
    )


@pytest.fixture
def app(container: AsyncContainer) -> ExtendedFastAPI:
    return ExtendedFastAPI(
        routers=(
            get_user_router(),
            get_company_router(),
        ),
        middleware_map=(*get_middleware_map(),),
        handling_map=(
            *get_handling_map(),
            *get_user_handling_map(),
        ),
        container=container,
        versions=VersionBundle(
            Version(str(DocsSettings.load().version.major)),
        ),
    )


@pytest_asyncio.fixture
async def app_in_lifespan(app: ExtendedFastAPI) -> AsyncGenerator[ASGIApp]:
    async with LifespanManager(app=app) as manager:
        yield manager.app


@pytest_asyncio.fixture
async def client(
    app_in_lifespan: ASGIApp, container: AsyncContainer
) -> AsyncGenerator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app_in_lifespan),
        base_url="http://coeffinance.com",
        timeout=(await container.get(ExternalAPISettings)).timeout,
    ) as client:
        yield client


@pytest.fixture(scope="package")
def postgresql() -> Generator[None]:
    pg = PostgresContainer("postgres:17.5", driver="asyncpg")
    pg.start()

    for key, value in (
        ("DB_USER", pg.username),
        ("DB_PASSWORD", pg.password),
        ("DB_HOST", pg.get_container_host_ip()),
        ("DB_PORT", str(pg.get_exposed_port(5432))),
        ("DB_NAME", pg.dbname),
    ):
        os.environ[key] = value

    command.upgrade(Config(toml_file="pyproject.toml"), "head")

    yield

    pg.stop()


@pytest_asyncio.fixture
async def sqlalchemy_session(
    container: AsyncContainer,
) -> AsyncGenerator[SQLAlchemySession]:
    async with container() as sub_container:
        yield await sub_container.get(SQLAlchemySession)


@pytest_asyncio.fixture
async def fastapi_pagination(
    container: AsyncContainer,
) -> FastAPIPagination[SQLAlchemySession, Select[Any]]:
    return await container.get(
        FastAPIPagination[SQLAlchemySession, Select[Any]]
    )


@pytest.fixture
def sqlalchemy_persistence(
    sqlalchemy_session: SQLAlchemySession,
) -> SQLAlchemyPersistence[SQLAlchemyPKModel]:
    return SQLAlchemyPersistence[SQLAlchemyPKModel](_session=sqlalchemy_session)


@pytest.fixture
def sqlalchemy_factories(
    request: FixtureRequest,
    sqlalchemy_persistence: SQLAlchemyPersistence[SQLAlchemyPKModel],
) -> Generator[tuple[type[ExtendedSQLAlchemyFactory[SQLAlchemyPKModel]]]]:
    factories = cast(
        tuple[type[ExtendedSQLAlchemyFactory[SQLAlchemyPKModel]]], request.param
    )

    for factory in factories:
        factory.__async_persistence__ = sqlalchemy_persistence  # pyright: ignore[reportGeneralTypeIssues] # Specifics of the lib design.

    yield factories

    for factory in factories:
        factory.__async_persistence__ = None  # pyright: ignore[reportGeneralTypeIssues] # Specifics of the lib design.


@pytest_asyncio.fixture
async def current_sqlalchemy_user_mock(
    app: ExtendedFastAPI,
) -> AsyncGenerator[SQLAlchemyUser]:
    user = SQLAlchemyUserFactory.build(is_active=True, is_verified=True)

    async def get_authenticated_override() -> SQLAlchemyUser:
        return user

    app.dependency_overrides[get_authenticated] = get_authenticated_override

    yield user

    app.dependency_overrides.clear()
