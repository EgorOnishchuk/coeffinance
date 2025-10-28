from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import override

from fastcrud import FastCRUD
from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from src.companies.db.models import SQLAlchemyCompany
from src.companies.schemas import (
    CompanyCreate,
    CompanyRead,
    CompanySearch,
    UserCompaniesSearch,
)
from src.core.db.sessions import DBSession, SQLAlchemySession
from src.core.errors import DBResponseError
from src.core.schemas import (
    BaseCursorPage,
    BaseOffsetPage,
    CursorSortingSearch,
)
from src.core.utils.paginators import (
    DBPaginator,
    Query,
)
from src.users.db.models import SQLAlchemyUser


@dataclass(kw_only=True, slots=True, frozen=True)
class CompanyDAO[SessionT: DBSession, QueryT: Query](ABC):
    _paginator: DBPaginator[SessionT, QueryT]

    @abstractmethod
    async def read_one(
        self,
        session: SessionT,
        company: CompanySearch,
    ) -> CompanyRead | None:
        pass

    @abstractmethod
    async def write_one(
        self,
        session: SessionT,
        company: CompanyCreate,
    ) -> CompanyRead | None:
        pass

    @abstractmethod
    async def read_by_user(
        self,
        session: SessionT,
        clauses: UserCompaniesSearch,
    ) -> BaseOffsetPage[CompanyRead]:
        pass

    @abstractmethod
    async def read_all(
        self,
        session: SessionT,
        clauses: CursorSortingSearch,
    ) -> BaseCursorPage[CompanyRead]:
        pass


# None is acceptable in accordance with the lib's coding style when the schema
# is absent or unknown:
# https://benavlabs.github.io/fastcrud/api/fastcrud/#__span-23-3.
type CompanyCrud = FastCRUD[  # type: ignore[type-var]
    SQLAlchemyCompany,
    CompanyCreate,
    None,  # pyright: ignore[reportInvalidTypeArguments]
    None,  # pyright: ignore[reportInvalidTypeArguments]
    None,  # pyright: ignore[reportInvalidTypeArguments]
    CompanyRead,
]


@dataclass(kw_only=True, slots=True, frozen=True)
class SQLAlchemyCompanyDAO(
    CompanyDAO[SQLAlchemySession, Select[tuple[SQLAlchemyCompany]]]
):
    _crud: CompanyCrud  # type: ignore[type-var] # None is acceptable in accordance with the lib's coding style when the schema is absent or unknown: https://benavlabs.github.io/fastcrud/api/fastcrud/#__span-23-3.

    @CompanyRead.from_instance_or_none  # type: ignore[arg-type] # MyPy doesn't support CoroutineType properly (unlike Pyright): https://github.com/python/mypy/issues/18635.
    @override
    async def read_one(
        self,
        session: SQLAlchemySession,
        company: CompanySearch,
    ) -> SQLAlchemyCompany | None:
        query = (
            select(SQLAlchemyCompany)
            .options(selectinload("*"))
            .where(
                SQLAlchemyCompany.brn == company.brn,
                SQLAlchemyCompany.country == str(company.country),
            )
        )

        return (await session.execute(query)).scalar_one_or_none()

    @CompanyRead.from_instance_or_none  # type: ignore[arg-type] # MyPy doesn't support CoroutineType properly (unlike Pyright): https://github.com/python/mypy/issues/18635.
    @override
    async def write_one(
        self,
        session: SQLAlchemySession,
        company: CompanyCreate,
    ) -> SQLAlchemyCompany | None:
        created = await self._crud.create(
            db=session,
            object=company,
            commit=False,
        )

        try:
            await session.flush()
        except DBResponseError as exc:
            if isinstance(exc.original, IntegrityError):
                return None
            raise

        await session.refresh(created)
        await session.load_all(created)
        return created

    @BaseOffsetPage[CompanyRead].from_instance  # type: ignore[arg-type] # MyPy doesn't support CoroutineType properly (unlike Pyright): https://github.com/python/mypy/issues/18635.
    @override
    async def read_by_user(
        self,
        session: SQLAlchemySession,
        clauses: UserCompaniesSearch,
    ) -> BaseOffsetPage[CompanyRead]:
        query = (
            (
                select(SQLAlchemyCompany).where(
                    SQLAlchemyCompany.users.any(
                        SQLAlchemyUser.nickname == clauses.user_nickname  # type: ignore[arg-type] # pyright: ignore[reportArgumentType] # A type checkers limitation when dealing with any().
                    )
                )
            ).options(selectinload("*"))
        ).order_by(getattr(SQLAlchemyCompany.score, clauses.order_by)())

        return await self._paginator.paginate_offset(
            session=session,
            query=query,
            search=clauses,
            return_schema=CompanyRead,
        )

    @BaseCursorPage[CompanyRead].from_instance  # type: ignore[arg-type] # MyPy doesn't support CoroutineType properly (unlike Pyright): https://github.com/python/mypy/issues/18635.
    @override
    async def read_all(
        self,
        session: SQLAlchemySession,
        clauses: CursorSortingSearch,
    ) -> BaseCursorPage[CompanyRead]:
        query = (
            (select(SQLAlchemyCompany))
            .options(selectinload("*"))
            .order_by(getattr(SQLAlchemyCompany.created_at, clauses.order_by)())
        )

        return await self._paginator.paginate_cursor(
            session=session,
            query=query,
            search=clauses,
            return_schema=CompanyRead,
        )
