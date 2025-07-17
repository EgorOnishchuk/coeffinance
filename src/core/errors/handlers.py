from fastapi import Request, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse

from src.core.deps.containers import container
from src.core.schemas import Error
from src.core.utils.loggers import Logger

validation_response: dict[int, dict[str, str | type[list[Error]]]] = {
    status.HTTP_422_UNPROCESSABLE_ENTITY: {
        "description": "Input does not match required format.",
        "model": list[Error],
    },
}

db_conn_response: dict[int, dict[str, str | type[Error]]] = {
    status.HTTP_503_SERVICE_UNAVAILABLE: {
        "description": "Failed to establish the connection to the database.",
        "model": Error,
    },
}

unexpected_exception_response: dict[int, dict[str, str | type[Error]]] = {
    status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "description": "An unexpected exception occurred that could not be classified.",
        "model": Error,
    },
}


def handle(errors: list[dict[str, str | list[str]]], status_code: int) -> JSONResponse:
    return JSONResponse(
        [Error(**content).model_dump(mode="json", exclude_none=True) for content in errors],
        status_code,
    )


async def validation_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    (await container.get(Logger)).debug(exc)

    return handle(
        [
            {
                "reason": f"{error['msg']}: {'.'.join(map(str, error['loc']))}.",
                "ways_to_solve": ["Correct your input."],
            }
            for error in exc.errors()
        ],
        status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


async def db_conn_handler(request: Request, exc: Exception) -> JSONResponse:
    (await container.get(Logger)).critical(exc)

    return handle(
        [{"reason": exc.args[0], "ways_to_solve": ["Try later."]}],
        status.HTTP_503_SERVICE_UNAVAILABLE,
    )


async def external_api_handler(request: Request, exc: Exception) -> JSONResponse:
    (await container.get(Logger)).exception(exc)

    return handle(
        [
            {
                "reason": exc.args[0],
                "ways_to_solve": ["Try later", "Contact with data provider."],
            },
        ],
        status.HTTP_503_SERVICE_UNAVAILABLE,
    )


async def route_not_found_handler(request: Request, exc: HTTPException) -> JSONResponse:
    (await container.get(Logger)).debug(exc)

    return handle(
        [{"reason": "Route not found.", "ways_to_solve": ["Check your route."]}],
        status.HTTP_404_NOT_FOUND,
    )


async def unexpected_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    (await container.get(Logger)).critical(exc)

    return handle(
        [{"reason": "Unexpected error.", "ways_to_solve": ["Try later."]}],
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
