from typing import Any, cast

from dishka import AnyOf, Provider, Scope, provide
from fastapi import Request
from fastcrud import FastCRUD
from sqlalchemy import Select

from src.companies.db.daos import CompanyCrud, CompanyDAO, SQLAlchemyCompanyDAO
from src.companies.db.models import SQLAlchemyCompany
from src.companies.service import CompanyService
from src.core.asgi import ExtendedRequest
from src.core.db.sessions import DBSession, SQLAlchemySession
from src.core.deps.base import BaseProvider
from src.core.utils.paginators import DBPaginator, Query


class SQLAlchemyCompanyDAOProvider(BaseProvider):
    @provide
    def get_fastcrud(
        self,
    ) -> CompanyCrud:  # type: ignore[type-var] # None is acceptable in accordance with the lib's coding style when the schema is absent or unknown: https://benavlabs.github.io/fastcrud/api/fastcrud/#__span-23-3.
        return FastCRUD(model=SQLAlchemyCompany)

    @provide(provides=AnyOf[CompanyDAO[DBSession, Query], SQLAlchemyCompanyDAO])
    def get_dao(
        self,
        paginator: DBPaginator[SQLAlchemySession, Select[Any]],
        crud: CompanyCrud,
    ) -> SQLAlchemyCompanyDAO:
        return SQLAlchemyCompanyDAO(_paginator=paginator, _crud=crud)


class CompanyServiceProvider(BaseProvider):
    @provide(scope=Scope.REQUEST)
    def get_service(
        self,
        request: Request,
        company_dao: CompanyDAO[DBSession, Query],
    ) -> CompanyService:
        request = cast(ExtendedRequest, request)
        return CompanyService(
            _container=request.app.state.dishka_container,
            _company_dao=company_dao,
        )


def get_company_deps() -> tuple[Provider, ...]:
    return (
        SQLAlchemyCompanyDAOProvider(),
        CompanyServiceProvider(),
    )
