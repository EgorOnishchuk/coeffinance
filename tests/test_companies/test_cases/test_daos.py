# pyright: reportUninitializedInstanceVariable=false
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from dishka import AsyncContainer
from pydantic_extra_types.country import CountryShortName

from src.companies.schemas import (
    CompanyLegals,
    Company,
    CompanyIdentity,
    UserCompaniesPagination,
)
from src.core.deps.paginators import SQLAlchemyFastAPIPaginatorProvider
from src.core.infrastructure.db_sessions import Session
from src.core.validators import (
    CursorPage,
    OffsetPage,
    CursorSortedPagination,
    OrderBy,
)
from tests.factories import CursorSortingSearchFactory
from tests.test_companies.factories import (
    CompanyCreateFactory,
    CompanySearchFactory,
    SQLAlchemyCompanyFactory,
    UserCompaniesSearchFactory,
)
from tests.test_users.factories import SQLAlchemyUserFactory


@pytest.mark.parametrize(
    "overridden_container",
    [(SQLAlchemyFastAPIPaginatorProvider(),)],
    indirect=True,
)
@pytest.mark.parametrize(
    "sqlalchemy_factories",
    [(SQLAlchemyCompanyFactory, SQLAlchemyUserFactory)],
    indirect=True,
)
@pytest.mark.usefixtures("postgresql")
class TestSQLAlchemyCompanyDAO:
    @pytest_asyncio.fixture(autouse=True)
    async def _setup(
        self,
        sqlalchemy_session: Session,
        overridden_container: AsyncContainer,
        sqlalchemy_factories: tuple[
            type[SQLAlchemyCompanyFactory], type[SQLAlchemyUserFactory]
        ],
    ) -> AsyncGenerator[None]:
        self._session = sqlalchemy_session
        self._dao = await overridden_container.get(SQLAlchemyCompanyDAO)

        self._company_factory, self._user_factory = sqlalchemy_factories
        self._company_factory.__set_relationships__ = True

        yield

        self._company_factory.__set_relationships__ = False

    @pytest.mark.asyncio
    async def test_read_one(self) -> None:
        expected = Company.model_validate(
            await self._company_factory.create_async()
        )
        actual = await self._dao.read_one(
            session=self._session,
            company=CompanyIdentity(
                brn=expected.brn, country=CountryShortName(expected.country)
            ),
        )

        assert actual is not None
        assert expected == actual

    @pytest.mark.asyncio
    async def test_read_not_found(
        self,
    ) -> None:
        actual = await self._dao.read_one(
            session=self._session, company=CompanySearchFactory.build()
        )

        assert actual is None

    @pytest.mark.asyncio
    async def test_write_one(
        self,
    ) -> None:
        expected = CompanyCreateFactory.build()
        actual = CompanyLegals.model_validate(
            await self._dao.write_one(
                session=self._session,
                company=expected,
            )
        )

        assert actual is not None
        assert expected == actual

    @pytest.mark.asyncio
    async def test_write_existing(self) -> None:
        existing = CompanyLegals.model_validate(
            await self._company_factory.create_async()
        )
        actual = await self._dao.write_one(
            session=self._session,
            company=existing,
        )

        assert actual is None

    @pytest.mark.asyncio
    async def test_read_by_user(
        self,
    ) -> None:
        user = await self._user_factory.create_async()
        size = 3
        expected = OffsetPage[Company](
            items=sorted(  # pyright: ignore[reportCallIssue] # Score is guaranteed not to be None, as it is defined at the factory.
                map(
                    Company.model_validate,
                    await self._company_factory.create_batch_async(
                        size, users=[user]
                    ),
                ),
                key=lambda company: company.score,  # pyright: ignore[reportArgumentType] # Score is guaranteed not to be None, as it is defined at the factory.
                reverse=True,
            ),
            total=size,
            page=1,
            size=size,
            pages=1,
        )

        actual = await self._dao.read_by_user(
            session=self._session,
            clauses=UserCompaniesPagination(
                user_nickname=user.nickname,
                order_by=OrderBy.DESC,
                page=1,
                size=size,
            ),
        )
        assert expected == actual

    @pytest.mark.asyncio
    async def test_read_by_user_empty(
        self,
    ) -> None:
        await self._company_factory.create_async(users=[])
        search = UserCompaniesSearchFactory.build()
        expected = OffsetPage[Company](
            items=[], total=0, page=1, size=search.size, pages=0
        )

        actual = await self._dao.read_by_user(
            session=self._session,
            clauses=search,
        )
        assert expected == actual

    @pytest.mark.asyncio
    async def test_read_all(self) -> None:
        size = 3
        expected = CursorPage[Company](
            items=sorted(
                map(
                    Company.model_validate,
                    await self._company_factory.create_batch_async(size),
                ),
                key=lambda company: company.created_at,
                reverse=True,
            ),
            total=size,
            current_page="Pg%3D%3D",
            previous_page=None,
            next_page=None,
        )

        actual = await self._dao.read_all(
            session=self._session,
            clauses=CursorSortedPagination(
                order_by=OrderBy.DESC,
                next_page=None,
                size=size,
            ),
        )
        assert expected == actual

    @pytest.mark.asyncio
    async def test_read_all_empty(
        self,
    ) -> None:
        expected = CursorPage[Company](
            items=[],
            total=0,
            current_page="Pg%3D%3D",
            previous_page=None,
            next_page=None,
        )

        actual = await self._dao.read_all(
            session=self._session,
            clauses=CursorSortingSearchFactory.build(),
        )
        assert expected == actual
