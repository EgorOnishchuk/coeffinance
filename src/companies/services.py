from dataclasses import dataclass

from dishka import AsyncContainer

from src.companies.infrastructure.api_clients import (
    CompanyAPIClient,
)
from src.companies.infrastructure.db_clients import (
    OneCompanyDBReader,
    OneCompanyDBWriter,
)
from src.companies.schemas import (
    CompanyIdentity,
    Company,
    CompanyIdentity,
    UserCompaniesPagination,
)
from src.core.errors import NotFoundError
from src.core.infrastructure.api_sessions import APISession
from src.core.infrastructure.db_sessions import DBSession
from src.core.validators import (
    CursorPage,
    OffsetPage,
    CursorSortedPagination,
)


@dataclass(kw_only=True, slots=True, frozen=True)
class CompanyCreateService[]


@dataclass(kw_only=True, slots=True, frozen=True)
class CompanyService:


    async def get_one(
        self,
        company: CompanyIdentity,
    ) -> Company:
        reader = await self._container.get(OneCompanyDBReader)

        async with self._container() as sub_container:
            read = await reader.read_one(
                session=await sub_container.get(DBSession),
                company=company,
            )

        if read is None:
            raise NotFoundError("Company not found in DB.")

        return read

    async def get_by_user(
        self,
        clauses: UserCompaniesPagination,
    ) -> OffsetPage[Company]:
        reader = await self._container.get(OneCompanyDBReader)

        async with self._container() as sub_container:
            return await reader.read_by_user(
                session=await sub_container.get(DBSession),
                clauses=clauses,
            )

    async def get_all(
        self,
        clauses: CursorSortedPagination,
    ) -> CursorPage[Company]:
        reader = await self._container.get(OneCompanyDBReader)

        async with self._container() as sub_container:
            return await reader.read_all(
                session=await sub_container.get(DBSession),
                clauses=clauses,
            )

    async def create(
        self,
        company: CompanyIdentity[str],
        api_client_type: type[CompanyAPIClient[CompanyIdentity[str]]],
    ) -> None:
        fetcher = await self._container.get(api_client_type)

        async with self._container() as sub_container:
            fetched = await fetcher.get_legals(
                session=await sub_container.get(APISession),
                company=company,
            )

        if fetched is None:
            raise NotFoundError("Company not found in external resources.")

        writer = await sub_container.get(OneCompanyDBWriter)

        async with self._container() as sub_container:
            is_written = await writer.write_one(
                session=await sub_container.get(DBSession),
                company=fetched,
            )

        if not is_written:
            raise AlreadyExistsError("Company already exists in DB.")
