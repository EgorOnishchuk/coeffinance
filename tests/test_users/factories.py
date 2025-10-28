from src.companies.db.models import SQLAlchemyCompany
from src.users.db.models import SQLAlchemyUser
from src.users.schemas import UserRead
from tests.factories import ExtendedPydanticFactory, ExtendedSQLAlchemyFactory


class UserReadFactory(ExtendedPydanticFactory[UserRead]):
    """
    Temporary solution until EmailStr support is added:
    https://github.com/litestar-org/polyfactory/issues/642.
    """

    @classmethod
    def email(cls) -> str:
        return cls.__faker__.free_email()


class SQLAlchemyUserFactory(ExtendedSQLAlchemyFactory[SQLAlchemyUser]):
    @classmethod
    def nickname(cls) -> str:
        return cls.__faker__.pystr(min_chars=6, max_chars=30)

    @classmethod
    def email(cls) -> str:
        return cls.__faker__.free_email()

    @classmethod
    def companies(cls) -> list[SQLAlchemyCompany]:
        from tests.test_companies.factories import SQLAlchemyCompanyFactory

        return cls._batch(SQLAlchemyCompanyFactory, min_=1, max_=5)
