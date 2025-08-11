from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from sqlalchemy import MetaData
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from src.core.errors import DBError


@runtime_checkable
class SQLAlchemyCompatible(Protocol):
    """
    SQLAlchemy and ORMs based on it (e.g. SQLModel).
    """

    metadata: MetaData


class DBManager(ABC):
    @abstractmethod
    async def clear(self) -> None:
        """
        In implementations, it's preferable to clean up the tables rather than drop the tables themselves for greater
        efficiency.
        """
        raise NotImplementedError


@dataclass(kw_only=True, slots=True, frozen=True)
class SQLAlchemyDBManager(DBManager):
    _engine: AsyncEngine
    _root_model: type[SQLAlchemyCompatible]

    async def clear(self) -> None:
        try:
            async with self._engine.begin() as conn:
                for table in self._root_model.metadata.sorted_tables:
                    await conn.execute(table.delete())
        except SQLAlchemyError as exc:
            raise DBError from exc
