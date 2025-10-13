from dataclasses import dataclass

from dishka import AsyncContainer

from src.companies.db.daos import CompanyDAO
from src.companies.schemas import (
    CompanyRead,
    UserCompaniesSearch,
)
from src.core.db.sessions import DBSession
from src.core.schemas import BaseCursorPage, BaseOffsetPage, CursorSortingSearch
from src.core.utils.paginators import (
    Query,
)


@dataclass(kw_only=True, slots=True, frozen=True)
class CompanyService:
    _container: AsyncContainer
    _company_dao: CompanyDAO[DBSession, Query]

    async def get_by_user(
        self,
        clauses: UserCompaniesSearch,
    ) -> BaseOffsetPage[CompanyRead]:
        async with self._container() as sub_container:
            return await self._company_dao.read_by_user(
                session=await sub_container.get(DBSession),
                clauses=clauses,
            )

    async def get_all(
        self,
        clauses: CursorSortingSearch,
    ) -> BaseCursorPage[CompanyRead]:
        async with self._container() as sub_container:
            return await self._company_dao.read_all(
                session=await sub_container.get(DBSession),
                clauses=clauses,
            )
