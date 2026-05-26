from __future__ import annotations

from collections.abc import (
    AsyncGenerator, Awaitable, Callable, Iterable,
    Sequence,
)
from contextlib import asynccontextmanager
from functools import wraps
from typing import Any, override

import sqlalchemy.exc
from sqlalchemy import Executable, Result, select, util
from sqlalchemy.engine.interfaces import _CoreAnyExecuteParams
from sqlalchemy.exc import (
    DisconnectionError,
    NoResultFound,
    SQLAlchemyError,
)
from tenacity import AsyncRetrying, RetryError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.ext.asyncio.session import _AS, _AsyncSessionContextManager, _T
from sqlalchemy.orm import selectinload
from sqlalchemy.orm._typing import OrmExecuteOptionsParameter
from sqlalchemy.orm.session import _BindArguments
from sqlalchemy.sql.selectable import ForUpdateParameter, TypedReturnsRows
from structlog.contextvars import bind_contextvars
from tenacity import retry, retry_if_exception_type, stop_after_attempt

from src.core.errors import DBConnError, DBResponseError
from src.core.infrastructure.db_models import SQLAlchemyModel, SQLAlchemyPKModel
from src.core.settings import ODDBSettings
from src.core.utils.logging import SQLAlchemyLog, SQLLog, bind


class Session(AsyncSession):
    @_handle
    async def execute(
        self,
        statement: TypedReturnsRows[_T],
        params: _CoreAnyExecuteParams | None = None,
        **kwargs: Any,
    ) -> Result[Any]:
        try:
            return await super().execute(
                statement,
                params,
                **kwargs,
            )
        except SQLAlchemyError:
            bind(SQLLog(statement=str(statement.compile()), params=params))
            raise

    @_handle
    async def flush(
        self, objects: Sequence[SQLAlchemyModel] | None = None
    ) -> None:
        try:
            await super().flush(objects)
        except SQLAlchemyError as exc:
            bind_contextvars(
                **dict(
                    SQLAlchemyLog(
                        objects=objects
                        if objects is not None
                        else list(self._marked)
                    )
                )
            )
            raise DBResponseError from exc

    @_handle
    async def refresh(
        self,
        instance: SQLAlchemyModel,
        attribute_names: Iterable[str] | None = None,
        with_for_update: ForUpdateParameter = None,
    ) -> None:
        try:
            await super().refresh(instance, attribute_names, with_for_update)
        except SQLAlchemyError as exc:
            bind_contextvars(**dict(SQLAlchemyLog(objects=[instance])))
            raise DBResponseError from exc

    @_handle
    async def commit(self) -> None:
        try:
            await super().commit()
        except SQLAlchemyError as exc:
            bind_contextvars(**dict(SQLAlchemyLog(objects=list(self._marked))))
            raise DBResponseError from exc

    @_handle
    async def rollback(self) -> None:
        try:
            await super().rollback()
        except SQLAlchemyError as exc:
            bind_contextvars(**dict(SQLAlchemyLog(objects=list(self._marked))))
            raise DBResponseError from exc

    async def load_all[Model: SQLAlchemyPKModel](
        self, instance: Model
    ) -> Model:
        query = (
            select(type(instance))
            .where(
                *(
                    column == value
                    for column, value in zip(
                        instance.pk_columns, instance.pk_values, strict=False
                    )
                )
            )
            .options(selectinload("*"))
        )

        try:
            return (await self.execute(query)).scalar_one()
        except DBResponseError as exc:
            if isinstance(exc.original, NoResultFound):
                exc.details.extend(
                    (
                        "Instance not found. The method is intended "
                        "for use after persisting the instance.",
                    )
                )
            raise

    @asynccontextmanager
    async def handle_transport(self) -> AsyncGenerator[None]:
        try:

                    yield
        except (sqlalchemy.exc.TimeoutError, DisconnectionError) as exc:
            raise DBConnError from exc


    @staticmethod
    def _handle[**P, ReturnT](
        func: Callable[P, Awaitable[ReturnT]],
    ) -> Callable[P, Awaitable[ReturnT]]:
        @wraps(func)
        @retry(

        )
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> ReturnT:
            try:
                return await func(*args, **kwargs)
            except


        return wrapper

    @property
    def _marked(self) -> set[SQLAlchemyModel]:
        return self.new | self.dirty | self.deleted
