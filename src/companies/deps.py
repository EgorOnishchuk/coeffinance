from dishka import AnyOf, Provider, Scope, provide

from src.companies.infrastructure.api_clients import (
    APIFNSClient,
    RussianCompanyLegalsAPIFetcher,
)
from src.companies.infrastructure.db_clients import (
    OneCompanyDBReader,
    OneCompanyDBWriter,
    SQLAlchemyCompanyClient,
)
from src.companies.services import (
    CompanyService,
)
from src.core.deps.base import CoreProvider, core_container
from src.core.settings import ExternalAPICredentials


class APIFNSClientProvider(CoreProvider):
    @provide
    def get_credentials(self) -> ExternalAPICredentials:
        return ExternalAPICredentials.load()

    client = provide(
        APIFNSClient,
        provides=AnyOf[RussianCompanyLegalsAPIFetcher, APIFNSClient],
    )


class SQLAlchemyCompanyClientProvider(CoreProvider):
    client = provide(
        SQLAlchemyCompanyClient,
        provides=AnyOf[
            OneCompanyDBReader, OneCompanyDBWriter, SQLAlchemyCompanyClient
        ],
    )


class CompanyServicesProvider(CoreProvider):
    @provide(scope=Scope.REQUEST)
    def get_service(
        self,
    ) -> CompanyService:
        return CompanyService(
            _container=core_container(),
        )


def get_company_deps() -> tuple[Provider, ...]:
    return (
        APIFNSClientProvider(),
        SQLAlchemyCompanyClientProvider(),
        CompanyServicesProvider(),
    )
