from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Final

from cadwyn import HeadVersion, Version, VersionBundle
from dishka import Provider, make_async_container

from src.companies.deps import get_company_deps
from src.companies.routes import get_company_router
from src.core.asgi import ExtendedFastAPI
from src.core.deps.base import get_deps
from src.core.errors import get_handling_map
from src.core.middlewares import get_middleware_map
from src.core.settings import (
    DocsSettings,
)
from src.users.deps import get_user_deps
from src.users.errors import (
    get_user_handling_map,
)
from src.users.routes import get_user_router


def get_prod_deps() -> tuple[Provider, ...]:
    return (
        *get_deps(),
        *get_user_deps(),
        *get_company_deps(),
    )


CONTAINER: Final = make_async_container(*get_prod_deps())


@asynccontextmanager
async def lifespan(app: ExtendedFastAPI) -> AsyncGenerator[None]:
    yield

    await app.state.dishka_container.close()


def get_app() -> ExtendedFastAPI:
    docs = DocsSettings.load()

    return ExtendedFastAPI(
        routers=(
            get_user_router(),
            get_company_router(),
        ),
        middleware_map=get_middleware_map(),
        handling_map=(
            *get_handling_map(),
            *get_user_handling_map(),
        ),
        container=CONTAINER,
        **docs.model_dump(by_alias=True, exclude_none=True),
        lifespan=lifespan,
        versions=VersionBundle(
            HeadVersion(),
            Version(str(docs.version.major)),
        ),
    )
