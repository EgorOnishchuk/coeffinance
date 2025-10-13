from src.analytics.db.models import SQLAlchemyAnalytics, SQLAlchemyRatio
from tests.factories import ExtendedSQLAlchemyFactory


class SQLAlchemyAnalyticsFactory(
    ExtendedSQLAlchemyFactory[SQLAlchemyAnalytics]
):
    @classmethod
    def name(cls) -> str:
        return cls.__faker__.pystr(min_chars=1, max_chars=30)

    @classmethod
    def ratios(cls) -> list[SQLAlchemyRatio]:
        return cls._batch(SQLAlchemyRatioFactory, min_=3, max_=20)


class SQLAlchemyRatioFactory(ExtendedSQLAlchemyFactory[SQLAlchemyRatio]):
    @classmethod
    def name(cls) -> str:
        return cls.__faker__.pystr(min_chars=1, max_chars=20)
