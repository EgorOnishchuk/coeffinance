from dataclasses import dataclass

from src.persons.data_access_layer import PersonDAL
from src.persons.schemas import Person
from src.persons.utils.clients import HTTPClient


@dataclass(kw_only=True, frozen=True, slots=True)
class PersonService:
    person_client: HTTPClient
    person_dal: PersonDAL

    async def get_all(self) -> list[Person]:
        return await self.person_dal.read_all()

    async def create_random(self) -> Person:
        person = await self.person_client.request("GET")

        return await self.person_dal.write(person)
