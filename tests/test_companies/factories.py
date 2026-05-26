# pyright: reportImportCycles=false
from decimal import Decimal
from typing import Any

from polyfactory import BaseFactory
from pydantic_extra_types.country import CountryShortName

from src.companies.infrastructure.db_models import SQLAlchemyCompany
from src.companies.schemas import (
    CompanyLegals,
    Company,
    Country,
    CompanyIdentity,
    UserCompaniesPagination,
)
from src.core.validators import CursorPage, OffsetPage
from src.reports.infrastructure.db_models import SQLAlchemyReport
from src.users.infrastructure.db_models import SQLAlchemyUser
from tests.factories import ExtendedPydanticFactory, ExtendedSQLAlchemyFactory
from tests.test_reports.factories import SQLAlchemyReportFactory
from tests.test_users.factories import SQLAlchemyUserFactory


def get_name(cls: type[BaseFactory[Any]]) -> str:
    return cls.__faker__.company()


def get_brn(cls: type[BaseFactory[Any]]) -> str:
    return cls.__faker__.pystr(min_chars=1, max_chars=100)


def get_country(cls: type[BaseFactory[Any]]) -> CountryShortName:
    return CountryShortName(str(cls.__random__.choice(tuple(Country))))


class CompanySearchFactory(ExtendedPydanticFactory[CompanyIdentity]):
    @classmethod
    def brn(cls) -> str:
        return get_brn(cls)

    @classmethod
    def country(cls) -> CountryShortName:
        return get_country(cls)


class CompanyCreateFactory(ExtendedPydanticFactory[CompanyLegals]):
    @classmethod
    def name(cls) -> str:
        return get_name(cls)

    @classmethod
    def brn(cls) -> str:
        return get_brn(cls)

    @classmethod
    def country(cls) -> CountryShortName:
        return get_country(cls)


class UserCompaniesSearchFactory(
    ExtendedPydanticFactory[UserCompaniesPagination]
):
    __use_defaults__ = True


class CompanyReadFactory(ExtendedPydanticFactory[Company]):
    @classmethod
    def country(cls) -> CountryShortName:
        return get_country(cls)


class CompanyBaseOffsetPageFactory(
    ExtendedPydanticFactory[OffsetPage[Company]]
):
    pass


class CompanyBaseCursorPageFactory(
    ExtendedPydanticFactory[CursorPage[Company]]
):
    pass


class SQLAlchemyCompanyFactory(ExtendedSQLAlchemyFactory[SQLAlchemyCompany]):
    @classmethod
    def name(cls) -> str:
        return get_name(cls)

    @classmethod
    def brn(cls) -> str:
        return get_brn(cls)

    @classmethod
    def score(cls) -> Decimal:
        return Decimal(cls.__random__.randrange(0, 101))

    @classmethod
    def users(cls) -> list[SQLAlchemyUser]:
        return cls._batch(SQLAlchemyUserFactory, min_=1, max_=10)

    @classmethod
    def reports(cls) -> list[SQLAlchemyReport]:
        return cls._batch(SQLAlchemyReportFactory, min_=1, max_=3)
