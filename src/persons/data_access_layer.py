from abc import ABC, abstractmethod
from typing import cast

from src.data_access_layer import AsyncpgDAL
from src.persons.schemas import Person, PersonCreate
from src.schemas import Schema, from_dict


class PersonDAL(ABC):
    @abstractmethod
    async def read_all(self) -> list[Person]:
        pass

    @abstractmethod
    @from_dict()
    @Schema.to_tuple
    async def write(self, person: PersonCreate) -> Person:
        pass


class PersonAsyncpgDAL(PersonDAL, AsyncpgDAL):
    schema = Person

    async def read_all(self) -> list[Person]:
        return await self._read_all()

    @from_dict()
    @Schema.to_tuple
    async def write(self, person: PersonCreate) -> Person:
        row = await self._conn.fetchrow(
            f"INSERT INTO {self.schema.__name__.lower()} (first_name, last_name, gender, birthdate) "  # noqa: S608
            "VALUES ($1, $2, $3, $4) RETURNING *",
            *person,
        )
        return cast(Person, row)
