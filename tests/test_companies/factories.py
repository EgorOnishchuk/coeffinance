# pyright: reportImportCycles=false
from decimal import Decimal
from typing import Any

from polyfactory import BaseFactory
from pydantic_extra_types.country import CountryShortName

from src.analytics.db.models import SQLAlchemyAnalytics
from src.companies.db.models import SQLAlchemyCompany
from src.companies.schemas import (
    CompanyCreate,
    CompanyRead,
    CompanySearch,
    Countries,
    UserCompaniesSearch,
)
from src.core.schemas import BaseCursorPage, BaseOffsetPage
from src.users.db.models import SQLAlchemyUser
from tests.factories import ExtendedPydanticFactory, ExtendedSQLAlchemyFactory
from tests.test_analytics.factories import SQLAlchemyAnalyticsFactory
from tests.test_users.factories import SQLAlchemyUserFactory


def get_name(cls: type[BaseFactory[Any]]) -> str:
    return cls.__faker__.company()


def get_brn(cls: type[BaseFactory[Any]]) -> str:
    return cls.__faker__.pystr(min_chars=1, max_chars=100)


def get_country(cls: type[BaseFactory[Any]]) -> CountryShortName:
    return CountryShortName(str(cls.__random__.choice(tuple(Countries))))


class CompanySearchFactory(ExtendedPydanticFactory[CompanySearch]):
    @classmethod
    def brn(cls) -> str:
        return get_brn(cls)

    @classmethod
    def country(cls) -> CountryShortName:
        return get_country(cls)


class CompanyCreateFactory(ExtendedPydanticFactory[CompanyCreate]):
    @classmethod
    def name(cls) -> str:
        return get_name(cls)

    @classmethod
    def brn(cls) -> str:
        return get_brn(cls)

    @classmethod
    def country(cls) -> CountryShortName:
        return get_country(cls)


class UserCompaniesSearchFactory(ExtendedPydanticFactory[UserCompaniesSearch]):
    __use_defaults__ = True


class CompanyReadFactory(ExtendedPydanticFactory[CompanyRead]):
    @classmethod
    def country(cls) -> CountryShortName:
        return get_country(cls)


class CompanyBaseOffsetPageFactory(
    ExtendedPydanticFactory[BaseOffsetPage[CompanyRead]]
):
    pass


class CompanyBaseCursorPageFactory(
    ExtendedPydanticFactory[BaseCursorPage[CompanyRead]]
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
    def analytics(cls) -> list[SQLAlchemyAnalytics]:
        return cls._batch(SQLAlchemyAnalyticsFactory, min_=1, max_=3)
