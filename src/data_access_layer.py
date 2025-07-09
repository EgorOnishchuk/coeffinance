from abc import ABC
from dataclasses import dataclass

from asyncpg import Connection, Record

from src.schemas import Schema, from_dicts


class DAL(ABC):
    schema: type[Schema]


@dataclass(kw_only=True, frozen=True, slots=True)
class AsyncpgDAL(DAL):
    _conn: Connection

    @from_dicts()
    async def _read_all(self) -> list[Record]:
        return await self._conn.fetch(f"SELECT * FROM {self.schema.__name__.lower()}")  # noqa: S608
