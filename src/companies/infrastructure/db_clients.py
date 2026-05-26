from dataclasses import dataclass
from typing import Protocol

import fastapi_pagination
from fastapi_pagination import Page, Params
from fastapi_pagination.config import Config
from fastapi_pagination.cursor import CursorParams
from fastapi_pagination.ext.sqlalchemy import apaginate
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from structlog.contextvars import unbind_contextvars

from src.companies.infrastructure.db_models import SQLAlchemyCompany
from src.companies.schemas import (
    Company,
    CompanyIdentity,
    CompanyLegals,
    UserCompaniesPagination,
)
from src.core.errors import DBResponseError
from src.core.infrastructure.db_models import get_sortables
from src.core.infrastructure.db_sessions import Session, SessionMaker
from src.core.utils.logging import SQLAlchemyLog
from src.core.validators import (
    CursorPage,
    CursorSortedPagination,
    OffsetPage,
)
from src.users.infrastructure.db_models import SQLAlchemyUser


class OneCompanyDBReader(Protocol):
    async def read_one(
        self,
        session: DBSession,
        company: CompanyIdentity,
    ) -> CompanyStored | None: ...


class UserCompaniesDBReader(Protocol):
    async def read_by_user(
        self,
        session: DBSession,
        clauses: UserCompaniesPagination,
    ) -> OffsetPage[CompanyStored]: ...


class AllCompaniesDBReader(Protocol):
    async def read_all(
        self,
        session: DBSession,
        clauses: CursorSortedPagination,
    ) -> CursorPage[CompanyStored]: ...


class OneCompanyDBWriter(Protocol):
    async def write_one(
        self,
        session: DBSession,
        company: CompanyLegals,
    ) -> bool: ...


@dataclass(kw_only=True, slots=True, frozen=True)
class SQLAlchemyCompanyClient:
    session_maker: SessionMaker[Session]

    @Company.from_instance  # https://github.com/python/mypy/issues/18635
    async def read_one(
        self,
        company: CompanyIdentity,
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

    async def write_one(
        self,
        session: Session,
        company: CompanyLegals,
    ) -> bool:
        written = SQLAlchemyCompany(**company.model_dump())
        session.add(written)

        try:
            await session.flush()
        except DBResponseError as exc:
            if isinstance(exc.original, IntegrityError):
                unbind_contextvars(SQLAlchemyLog.namespace)
                return False

            raise

        return True

    @OffsetPage[Company].from_instance
    async def read_by_user(
        self,
        session: Session,
        clauses: UserCompaniesPagination,
    ) -> Page[Company]:
        query = (
            (
                select(SQLAlchemyCompany).where(
                    SQLAlchemyCompany.users.any(
                        SQLAlchemyUser.nickname == clauses.user_nickname  # type: ignore[arg-type] # pyright: ignore[reportArgumentType]
                    )
                )
            ).options(selectinload("*"))
        ).order_by(
            *get_sortables((SQLAlchemyCompany.score,), (clauses.order_by,))
        )

        return await apaginate(
            conn=session,
            query=query,
            params=Params(page=clauses.page, size=clauses.size),
            config=Config(page_cls=Page[Company]),
        )

    @CursorPage[Company].from_instance
    async def read_all(
        self,
        session: Session,
        clauses: CursorSortedPagination,
    ) -> CursorPage[Company]:
        query = (
            (select(SQLAlchemyCompany))
            .options(selectinload("*"))
            .order_by(
                *get_sortables(
                    (SQLAlchemyCompany.created_at,), (clauses.order_by,)
                )
            )
        )

        return await apaginate(
            conn=session,
            query=query,
            params=CursorParams(cursor=clauses.next_page, size=clauses.size),
            config=Config(
                page_cls=fastapi_pagination.cursor.CursorPage[Company]
            ),
        )
