# mypy: disable-error-code="attr-defined"
# pyright: reportAttributeAccessIssue=false, reportUninitializedInstanceVariable=false
# Mocks are not supported: https://github.com/python/mypy/issues/1188, https://github.com/microsoft/pyright/discussions/5311.


import pytest
import pytest_asyncio
from httpx import AsyncClient

from src.companies.schemas import UserCompaniesSearch
from src.companies.service import CompanyService
from src.core.asgi import Architecture
from src.core.settings import DocsSettings
from src.users.db.models import SQLAlchemyUser
from tests.factories import (
    CursorSortingSearchFactory,
    OffsetSortingSearchFactory,
)


class TestCompanyRouter:
    ROOT = (
        f"/{Architecture.JSON_API}/"
        f"{DocsSettings.load().version.major}/companies"
    )

    @pytest_asyncio.fixture(autouse=True)
    async def _setup(
        self,
        client: AsyncClient,
        company_service: CompanyService,
        current_sqlalchemy_user_mock: SQLAlchemyUser,
    ) -> None:
        self._client = client
        self._expected = company_service
        self._user = current_sqlalchemy_user_mock

    @pytest.mark.asyncio
    async def test_my_companies(self) -> None:
        search = OffsetSortingSearchFactory.build().model_dump(by_alias=True)
        actual = await self._client.get(
            f"{self.ROOT}/my",
            params=search,
        )

        self._expected.get_by_user.assert_awaited_once_with(
            clauses=UserCompaniesSearch(
                user_nickname=self._user.nickname,
                **search,
            )
        )
        assert (
            self._expected.get_by_user.return_value.model_dump(
                by_alias=True,
                mode="json",
            )
            == actual.json()
        )

    @pytest.mark.asyncio
    async def test_all_companies(self) -> None:
        search = CursorSortingSearchFactory.build()
        actual = await self._client.get(
            f"{self.ROOT}/all",
            params=search.model_dump(by_alias=True),
        )

        self._expected.get_all.assert_awaited_once_with(
            clauses=search,
        )
        assert (
            self._expected.get_all.return_value.model_dump(
                by_alias=True,
                mode="json",
            )
            == actual.json()
        )
