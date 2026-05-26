# pyright: reportImportCycles=false


from dishka import (
    AsyncContainer,
    Provider,
    Scope,
    make_async_container,
)
from dishka.integrations.fastapi import FastapiProvider

from src.companies.deps import get_company_deps
from src.users.deps import get_user_deps


class CoreProvider(Provider):
    scope = Scope.APP


def get_core_deps() -> tuple[Provider, ...]:
    from src.core.deps.api_sessions import HTTPXProvider
    from src.core.deps.db_sessions import (
        RedisProvider,
        SQLAlchemyProvider,
    )
    from src.core.deps.mail_sessions import AIOSMTPLibProvider
    from src.core.deps.paginators import SQLAlchemyFastAPIPaginatorProvider

    return (
        FastapiProvider(),
        SQLAlchemyProvider(),
        SQLAlchemyFastAPIPaginatorProvider(),
        RedisProvider(),
        AIOSMTPLibProvider(),
        HTTPXProvider(),
    )


def get_prod_deps() -> tuple[Provider, ...]:
    return (
        *get_core_deps(),
        *get_user_deps(),
        *get_company_deps(),
    )


def core_container() -> AsyncContainer:
    return make_async_container(*get_prod_deps())
