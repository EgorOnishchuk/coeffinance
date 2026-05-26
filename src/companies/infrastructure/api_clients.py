from http import HTTPMethod
from typing import ClassVar, Final, Protocol

from httpx import URL
from pydantic import ValidationError

from src.companies.errors import CompanyNotFoundError
from src.companies.infrastructure.api_models import APIFNSLegalEntities
from src.companies.schemas import (
    CompanyBRN, CompanyIdentity,
    CompanyLegals,
    Country,
    RussianCompanyBRN,
)
from src.core.errors import ExternalAPIResponseError
from src.core.infrastructure.api_sessions import Sessionmaker
from src.core.settings import ExternalAPICredentials
from src.core.utils.retries import http_retry


class CompanyAPIClient(Protocol):
    async def get_legals(
        self,
        company: CompanyBRN,
    ) -> CompanyLegals: ...


class APIFNSClient(CompanyAPIClient):
    sessionmaker: Sessionmaker

    _host: Final[ClassVar] = "api-fns.ru"

    @http_retry
    async def get_legals(
        self,
        company: CompanyBRN,
    ) -> CompanyLegals:
        filters = (
            "active",
            "onlyul",
        )

        async with self.sessionmaker as session:
            json = await session.fetch_resource(
                URL(
                    host=self._host,
                    path="/api/search",
                ),
                "POST",
                body={
                    "q": company.brn,
                    "filter": "+".join(filters),
                    "key": ExternalAPICredentials().fns_key,
                },
            )

        try:
            entities = APIFNSLegalEntities(**json)
        except ValidationError as exc:
            raise ExternalAPIResponseError from exc

        if not entities.count:
            raise CompanyNotFoundError

        return CompanyLegals(
            **entities.items[0].entity.model_dump(),
            country="RUS",
        )
