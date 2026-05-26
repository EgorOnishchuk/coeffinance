from datetime import date

from polyfactory.decorators import post_generated

from src.reports.infrastructure.db_models import (
    SQLAlchemyRatio,
    SQLAlchemyReport,
)
from tests.factories import ExtendedSQLAlchemyFactory


class SQLAlchemyReportFactory(ExtendedSQLAlchemyFactory[SQLAlchemyReport]):
    @classmethod
    def name(cls) -> str:
        return cls.__faker__.pystr(min_chars=1, max_chars=30)

    @classmethod
    def ratios(cls) -> list[SQLAlchemyRatio]:
        return cls._batch(SQLAlchemyRatioFactory, min_=3, max_=20)

    @post_generated
    @classmethod
    def period_end(cls, period_start: date) -> date:
        return cls.__faker__.date_between(period_start, "+1y")


class SQLAlchemyRatioFactory(ExtendedSQLAlchemyFactory[SQLAlchemyRatio]):
    @classmethod
    def name(cls) -> str:
        return cls.__faker__.pystr(min_chars=1, max_chars=20)
