# pyright: reportImportCycles=false

import logging

from dishka import Provider, Scope, provide
from dishka.integrations.fastapi import FastapiProvider

from src.core.utils.loggers import UVICORN_LOGGER, Logger


class BaseProvider(Provider):
    scope = Scope.APP


class UvicornLoggerProvider(BaseProvider):
    @provide(provides=Logger)
    def get_logger(self) -> logging.Logger:
        return logging.getLogger(UVICORN_LOGGER)


def get_deps() -> tuple[Provider, ...]:
    from src.core.deps.db import RedisProvider, SQLAlchemyProvider
    from src.core.deps.external_api import HTTPXProvider
    from src.core.deps.mail import AIOSMTPLibProvider
    from src.core.deps.paginators import FastAPIPaginationProvider

    return (
        FastapiProvider(),
        UvicornLoggerProvider(),
        SQLAlchemyProvider(),
        FastAPIPaginationProvider(),
        RedisProvider(),
        AIOSMTPLibProvider(),
        HTTPXProvider(),
    )
