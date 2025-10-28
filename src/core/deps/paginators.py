from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

from dishka import AnyOf, provide
from fastapi_pagination.ext.sqlalchemy import (
    AsyncConn,
    Selectable,
    UnwrapMode,
    apaginate,
)
from sqlalchemy import Select

from src.core.db.sessions import SQLAlchemySession
from src.core.deps.base import BaseProvider
from src.core.utils.paginators import DBPaginator, FastAPIPagination, Paginate

if TYPE_CHECKING:
    from fastapi_pagination.bases import AbstractParams
    from fastapi_pagination.config import Config
    from fastapi_pagination.types import AdditionalData, AsyncItemsTransformer


class SQLAlchemyPaginate(Protocol):
    """
    Since it is impossible to effectively extract the signature for
    annotation from any method in Python, it must be duplicated.
    """

    async def __call__(  # noqa: PLR0913
        self,
        conn: AsyncConn,
        query: Selectable,
        params: AbstractParams | None = None,
        *,
        count_query: Selectable | None = None,
        subquery_count: bool = True,
        unwrap_mode: UnwrapMode | None = None,
        transformer: AsyncItemsTransformer | None = None,
        additional_data: AdditionalData | None = None,
        unique: bool = True,
        config: Config | None = None,
    ) -> Any:
        pass


class FastAPIPaginationProvider(BaseProvider):
    @provide(provides=Paginate[SQLAlchemySession, Select[Any], ...])
    def get_paginate(
        self,
    ) -> SQLAlchemyPaginate:
        return apaginate

    @provide(
        provides=AnyOf[
            DBPaginator[SQLAlchemySession, Select[Any]],
            FastAPIPagination[SQLAlchemySession, Select[Any]],
        ]
    )
    def get_paginator(
        self,
        paginate: Paginate[SQLAlchemySession, Select[Any], ...],
    ) -> FastAPIPagination[SQLAlchemySession, Select[Any]]:
        return FastAPIPagination[SQLAlchemySession, Select[Any]](
            _paginate=paginate
        )
