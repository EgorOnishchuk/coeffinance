from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncEngine


@runtime_checkable
class SQLAlchemyCompatible(Protocol):
    """
    SQLAlchemy and ORMs based on it (e.g. SQLModel).
    """

    metadata: MetaData


class DBManager(ABC):
    @abstractmethod
    async def setup(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def clear(self) -> None:
        raise NotImplementedError


@dataclass(kw_only=True, slots=True, frozen=True)
class SQLAlchemyDBManager(DBManager):
    engine: AsyncEngine
    root_model: type[SQLAlchemyCompatible]

    async def setup(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(self.root_model.metadata.create_all)

    async def clear(self) -> None:
        async with self.engine.begin() as conn:
            for table in self.root_model.metadata.sorted_tables:
                await conn.execute(table.delete())
