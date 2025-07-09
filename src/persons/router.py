from fastapi import status
from fastapi.routing import APIRouter

from src.errors import db_conn_response, unexpected_exception_response
from src.persons.dependencies import PersonServiceDep
from src.persons.schemas import Person
from src.schemas import Error

router = APIRouter(prefix="/persons", tags=["Persons"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="All persons retrieval.",
    response_description="All persons are successfully retrieved.",
    responses={**db_conn_response, **unexpected_exception_response},
)
async def get_all(person_service: PersonServiceDep) -> list[Person]:
    """Retrieves and returns all stored persons."""
    return await person_service.get_all()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="A random person creation.",
    response_description="A random person is successfully created.",
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "A random person could have been created, but it could not be retrieved due to the "
            "external API not being available.",
            "model": Error,
        },
        **db_conn_response,
        **unexpected_exception_response,
    },
)
async def create_random(person_service: PersonServiceDep) -> Person:
    """Creates, saves and returns a random person retrieved from an external API."""
    return await person_service.create_random()
