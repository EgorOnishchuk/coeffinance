from abc import ABC
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from functools import wraps
from typing import Any, Final

import sqlalchemy.exc
from sqlalchemy import select
from sqlalchemy.exc import (
    DisconnectionError,
    SQLAlchemyError,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from tenacity import retry, retry_if_exception_type, stop_after_attempt

from src.core.db.models import SQLAlchemyPKModel
from src.core.errors import DBConnError, DBResponseError
from src.core.settings import DBSettings


@dataclass(kw_only=True, slots=True)
class DBSession(ABC):
    _settings: Final[DBSettings]  # type: ignore[misc] # A MyPy limitation when dealing with dataclasses with Final, not confirmed by Pyright: https://github.com/python/mypy/issues/5608.


class SQLAlchemySession(AsyncSession, DBSession):
    def __init__(self, settings: DBSettings, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        DBSession.__init__(self, _settings=settings)

        retryer: Final = retry(
            retry=retry_if_exception_type(DBConnError),
            stop=stop_after_attempt(self._settings.retries),
            reraise=True,
        )

        for method in (
            "execute",
            "get",
            "merge",
            "flush",
            "refresh",
            "load_all",
            "commit",
            "rollback",
        ):
            setattr(self, method, retryer(self.handle(getattr(self, method))))

    @staticmethod
    def handle[**P, ReturnT](
        func: Callable[P, Awaitable[ReturnT]],
    ) -> Callable[P, Awaitable[ReturnT]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> ReturnT:
            try:
                return await func(*args, **kwargs)
            except (sqlalchemy.exc.TimeoutError, DisconnectionError) as exc:
                raise DBConnError(code=exc.code) from exc
            except SQLAlchemyError as exc:
                raise DBResponseError(code=exc.code) from exc

        return wrapper

    async def load_all[Model: SQLAlchemyPKModel](
        self, instance: Model
    ) -> Model:
        """
        There is no way to «eagerly» refresh an object, so it is necessary to
        manually load relationships.
        """
        cls = type(instance)

        query = (
            select(cls)
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

        return (await self.execute(query)).scalar_one()
