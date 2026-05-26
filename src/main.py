import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from cadwyn import Version, VersionBundle
from fastapi import FastAPI

from src.companies.routers import company_router
from src.core.asgi import FastAPIExtended
from src.core.deps.base import core_container
from src.core.errors import core_exc_handlers, sys_handler
from src.core.middlewares import core_middleware
from src.core.settings import (
    DocsSettings,
)
from src.core.utils.logging import setup
from src.users.routes import user_router

setup()
sys.excepthook = sys_handler


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    yield

    await core_container().close()


def core_app() -> FastAPIExtended:
    return FastAPIExtended(
        routers=(
            user_router(),
            company_router(),
        ),
        middleware=(*core_middleware(),),
        exception_handlers={
            *core_exc_handlers(),
        },
        container=core_container(),
        lifespan=lifespan,
        versions=VersionBundle(
            Version(str(DocsSettings().version.major)),
        ),
        title=DocsSettings().title,
        summary=DocsSettings().summary,
        description=DocsSettings().description,
        version=str(DocsSettings().version),
        license_info=DocsSettings().license,
    )
