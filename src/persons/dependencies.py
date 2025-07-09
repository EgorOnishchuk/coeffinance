from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from src.dependencies import ConnDep
from src.persons.data_access_layer import PersonAsyncpgDAL, PersonDAL
from src.persons.schemas import PersonCreate
from src.persons.service import PersonService
from src.persons.utils.clients import HTTPClient


@lru_cache
def get_fakerapi_client() -> HTTPClient:
    return HTTPClient(
        url="https://fakerapi.it/api/v2/persons?_quantity=1",
        schema=PersonCreate,
    )


FakerAPIClientDep = Annotated[HTTPClient, Depends(get_fakerapi_client)]


@lru_cache
def get_person_asyncpg_dal(conn: ConnDep) -> PersonAsyncpgDAL:
    return PersonAsyncpgDAL(_conn=conn)


PersonAsyncpgDALDep = Annotated[PersonDAL, Depends(get_person_asyncpg_dal)]


@lru_cache
def get_person_service(
    person_client: FakerAPIClientDep,
    person_dal: PersonAsyncpgDALDep,
) -> PersonService:
    return PersonService(person_client=person_client, person_dal=person_dal)


PersonServiceDep = Annotated[PersonService, Depends(get_person_service)]
