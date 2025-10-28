from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import (
    Any,
    Concatenate,
    cast,
    override,
)

from fastapi_pagination import Page, Params, set_page, set_params
from fastapi_pagination.cursor import CursorPage, CursorParams
from sqlalchemy import Select

from src.core.db.sessions import DBSession
from src.core.schemas import (
    BaseCursorPage,
    BaseOffsetPage,
    CursorSearch,
    OffsetSearch,
    Schema,
)


class FastAPIPaginationOffsetPage[SchemaT: Schema](
    Page[SchemaT], BaseOffsetPage[SchemaT]
):
    pass


class FastAPIPaginationCursorPage[SchemaT: Schema](  # type: ignore[misc] # Specifics of the lib implementation. Does not affect anything in runtime.
    CursorPage[SchemaT], BaseCursorPage[SchemaT]
):
    pass


type Query = Select[Any]


class DBPaginator[SessionT: DBSession, QueryT: Query](ABC):
    @abstractmethod
    async def paginate_offset[SchemaT: Schema](
        self,
        session: SessionT,
        query: QueryT,
        search: OffsetSearch,
        return_schema: type[SchemaT],
        *args: Any,
        **kwargs: Any,
    ) -> BaseOffsetPage[SchemaT]:
        raise NotImplementedError

    @abstractmethod
    async def paginate_cursor[SchemaT: Schema](
        self,
        session: SessionT,
        query: QueryT,
        search: CursorSearch,
        return_schema: type[SchemaT],
        *args: Any,
        **kwargs: Any,
    ) -> BaseCursorPage[SchemaT]:
        raise NotImplementedError


type Paginate[
    SessionT: DBSession,
    QueryT: Query,
    **P,
] = Callable[
    Concatenate[SessionT, QueryT, P],
    Awaitable[BaseCursorPage[Schema] | BaseOffsetPage[Schema]],
]


@dataclass(kw_only=True, slots=True, frozen=True)
class FastAPIPagination[SessionT: DBSession, QueryT: Query](
    DBPaginator[SessionT, QueryT]
):
    _paginate: Paginate[SessionT, QueryT, ...]

    @override
    async def paginate_offset[SchemaT: Schema](
        self,
        session: SessionT,
        query: QueryT,
        search: OffsetSearch,
        return_schema: type[SchemaT],
        *args: Any,
        **kwargs: Any,
    ) -> BaseOffsetPage[SchemaT]:
        set_page(FastAPIPaginationOffsetPage[return_schema])  # type: ignore[valid-type] # The lib API design specifics.
        set_params(Params(**search.model_dump(include={"page", "size"})))

        return cast(
            FastAPIPaginationOffsetPage[return_schema],  # type: ignore[valid-type] # pyright: ignore[reportInvalidTypeForm] # The lib API design specifics.
            await self._paginate(session, query, *args, **kwargs),
        )

    @override
    async def paginate_cursor[SchemaT: Schema](
        self,
        session: SessionT,
        query: QueryT,
        search: CursorSearch,
        return_schema: type[SchemaT],
        *args: Any,
        **kwargs: Any,
    ) -> BaseCursorPage[SchemaT]:
        set_page(FastAPIPaginationCursorPage[return_schema])  # type: ignore[valid-type] # The lib API design specifics.
        set_params(
            CursorParams(**search.model_dump(include={"cursor", "size"}))
        )

        return cast(
            FastAPIPaginationCursorPage[return_schema],  # type: ignore[valid-type] # pyright: ignore[reportInvalidTypeForm] # The lib API design specifics.
            await self._paginate(session, query, *args, **kwargs),
        )
