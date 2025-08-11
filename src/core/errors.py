from abc import ABC
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import TYPE_CHECKING, ParamSpec

if TYPE_CHECKING:
    from dishka import AsyncContainer
from fastapi import Request, Response, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse

from src.core.schemas import Error
from src.core.utils.loggers import Logger


class OpenAPIError(Exception):
    def __init__(self, key: str) -> None:
        super().__init__(f"{key} object is not found.")


class DetailedError(Exception, ABC):
    """
    Provides an additional context to responses that do not allow for a clear determination of an error at
    the protocol level. For example, HTTP 401 Unauthorized does not require a response body, as the meaning of the error
    is clear from its code, while 400 Bad Request does require one.
    """

    def __init__(self, msg: str, ways_to_solve: tuple[str, ...]) -> None:
        super().__init__(msg)
        self.ways_to_solve = ways_to_solve


class DBError(Exception):
    pass


class EmailConnError(DetailedError, ConnectionError):
    def __init__(
        self,
        msg: str = "Email service error.",
        ways_to_solve: tuple[str, ...] = (
            "Check that the email is valid and is not compromised, blocked or deleted.",
            "Try later.",
            "Contact with Support or the mail server provider.",
        ),
    ) -> None:
        super().__init__(msg, ways_to_solve)


class ExternalAPIError(DetailedError, ConnectionError):
    def __init__(
        self,
        msg: str = "External service error.",
        ways_to_solve: tuple[str, ...] = ("Try later.", "Contact with Support or the data provider."),
    ) -> None:
        super().__init__(msg, ways_to_solve)


P = ParamSpec("P")


def serialize(func: Callable[P, Awaitable[tuple[Error, int]]]) -> Callable[P, Awaitable[JSONResponse]]:
    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> JSONResponse:
        error, code = await func(*args, **kwargs)
        return JSONResponse(content=error.model_dump(mode="json"), status_code=code)

    return wrapper


@serialize
async def validation_handler(
    request: Request,
    exc: RequestValidationError,
) -> tuple[Error, int]:
    container: AsyncContainer = request.app.state.dishka_container
    (await container.get(Logger)).debug(exc)

    return Error(
        reason="Invalid input.",
        ways_to_solve=tuple(f"{error['msg']}: {'.'.join(map(str, error['loc']))}" for error in exc.errors()),
    ), status.HTTP_422_UNPROCESSABLE_ENTITY


async def db_conn_handler(request: Request, exc: DBError) -> Response:
    container: AsyncContainer = request.app.state.dishka_container
    (await container.get(Logger)).critical(exc)

    return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@serialize
async def email_conn_handler(request: Request, exc: EmailConnError) -> tuple[Error, int]:
    container: AsyncContainer = request.app.state.dishka_container
    (await container.get(Logger)).exception(exc)

    return Error(reason=exc.args[0], ways_to_solve=exc.ways_to_solve), status.HTTP_503_SERVICE_UNAVAILABLE


@serialize
async def external_api_handler(request: Request, exc: ExternalAPIError) -> tuple[Error, int]:
    container: AsyncContainer = request.app.state.dishka_container
    (await container.get(Logger)).exception(exc)

    return Error(reason=exc.args[0], ways_to_solve=exc.ways_to_solve), status.HTTP_503_SERVICE_UNAVAILABLE


# The errors below do not require a body (see the example from the DetailedExc docs at the beginning of the file), but
# without overriding FastAPI will still add JSON with «detail» to them.


async def unauthenticated_handler(request: Request, exc: HTTPException) -> Response:
    container: AsyncContainer = request.app.state.dishka_container
    (await container.get(Logger)).debug(exc)

    return Response(status_code=status.HTTP_401_UNAUTHORIZED)


async def unauthorized_handler(request: Request, exc: HTTPException) -> Response:
    container: AsyncContainer = request.app.state.dishka_container
    (await container.get(Logger)).exception(exc)

    return Response(status_code=status.HTTP_403_FORBIDDEN)


async def not_found_handler(request: Request, exc: HTTPException) -> Response:
    container: AsyncContainer = request.app.state.dishka_container
    (await container.get(Logger)).debug(exc)

    return Response(status_code=status.HTTP_404_NOT_FOUND)


async def unexpected_exception_handler(
    request: Request,
    exc: Exception,
) -> Response:
    container: AsyncContainer = request.app.state.dishka_container
    (await container.get(Logger)).critical(exc)

    return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
