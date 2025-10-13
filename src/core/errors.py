from abc import ABC
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Final, TypeVar

from fastapi import Response, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse

from src.core.asgi import ExtendedRequest, HandlingPair
from src.core.schemas import JSON, PublicError
from src.core.utils.loggers import Logger


class NonDetailedError(Exception, ABC):
    def __init__(self, msg: str) -> None:
        super().__init__(msg)
        self.msg: Final = msg

    @property
    def original(self) -> BaseException | None:
        return self.__cause__ or self.__context__


class DetailedError(NonDetailedError, ABC):
    """
    Allows the user to find and possibly even fix the error themselves. If this
    is not possible, it clearly indicates the malfunctioning feature so that
    the user can continue to use the rest of the app's features.
    """

    def __init__(
        self, sys_msg: str, *, user_msg: str, ways_to_solve: tuple[str, ...]
    ) -> None:
        super().__init__(sys_msg)
        self.user_msg: Final = user_msg
        self.ways_to_solve: Final = ways_to_solve


# Pure system exceptions.


class OpenAPIError(NonDetailedError):
    def __init__(self, key: str) -> None:
        super().__init__(f"{key} object is not in the Schema.")
        self.key: Final = key


class DBConnError(NonDetailedError, ConnectionError):
    def __init__(
        self,
        *,
        code: str | None = None,
    ) -> None:
        super().__init__(
            f"DB is unavailable{f': {code}' if code is not None else ''}."
        )
        self.code: Final = code


class ExternalAPIConnError(DetailedError, ConnectionError):
    def __init__(
        self,
        sys_msg: str,
        *,
        user_msg: str = "External service is unavailable.",
        ways_to_solve: tuple[str, ...] = (
            "Try later.",
            "Contact with Support or the data provider.",
        ),
    ) -> None:
        super().__init__(
            sys_msg, user_msg=user_msg, ways_to_solve=ways_to_solve
        )


class EmailConnError(DetailedError, ConnectionError):
    def __init__(
        self,
        sys_msg: str,
        *,
        user_msg: str = "Email service is unavailable.",
        ways_to_solve: tuple[str, ...] = (
            "Try later.",
            "Contact with Support or the mail server provider.",
        ),
    ) -> None:
        super().__init__(
            sys_msg, user_msg=user_msg, ways_to_solve=ways_to_solve
        )


# Business exceptions. However, they can act as system exceptions when the
# request is guaranteed to be valid, and at the same time the contract does not
# anticipate a business error, but it nevertheless appears.


class DBResponseError(NonDetailedError):
    def __init__(self, *, code: str | None = None) -> None:
        super().__init__(
            f"DB failed to execute the request"
            f"{f': {code}' if code is not None else ''}."
        )
        self.code: Final = code


class ExternalAPIResponseError(DetailedError, ABC):
    def __init__(
        self,
        sys_msg: str,
        *,
        code: int | str | None = None,
        user_msg: str = "External service is unavailable.",
        ways_to_solve: tuple[str, ...] = (
            "Try later.",
            "Contact with the data provider.",
        ),
    ) -> None:
        super().__init__(
            f"The response was unsuccessful: {sys_msg} ({code}).",
            user_msg=user_msg,
            ways_to_solve=ways_to_solve,
        )
        self.code: Final = code


class ExternalRESTResponseError(ExternalAPIResponseError):
    def __init__(
        self,
        json: JSON | None = None,
        *,
        code: int,
        user_msg: str = "External service is unavailable.",
        ways_to_solve: tuple[str, ...] = (
            "Try later.",
            "Contact with the data provider.",
        ),
    ) -> None:
        super().__init__(
            f"The response was unsuccessful: {json} ({code}).",
            user_msg=user_msg,
            ways_to_solve=ways_to_solve,
            code=self.code,
        )
        self.json: Final = json


class EmailResponseError(DetailedError):
    def __init__(
        self,
        sys_msg: str,
        *,
        code: str | int | None = None,
        user_msg: str = "Email service is unavailable.",
        ways_to_solve: tuple[str, ...] = (
            "Check that the email is valid and is not compromised, blocked or "
            "deleted.",
            "Try later.",
            "Contact with Support or the mail server provider.",
        ),
    ) -> None:
        super().__init__(
            f"The response was unsuccessful: {sys_msg} ({code}).",
            user_msg=user_msg,
            ways_to_solve=ways_to_solve,
        )
        self.code: Final = code


def serialize[**P](
    func: Callable[P, Awaitable[tuple[PublicError, int]]],
) -> Callable[P, Awaitable[JSONResponse]]:
    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> JSONResponse:
        error, code = await func(*args, **kwargs)
        return JSONResponse(
            content=error.model_dump(mode="json"), status_code=code
        )

    return wrapper


# These handlers provide an additional context to responses that do not allow
# for a clear determination of an error at the protocol level. For example,
# HTTP 404 Not Found does not require a response body, as the meaning of the
# error is clear from its code, while 422 Unprocessable Entity does require
# one.


@serialize
async def validation_handler(
    request: ExtendedRequest,
    exc: RequestValidationError,
) -> tuple[PublicError, int]:
    (await request.state.dishka_container.get(Logger)).debug(exc)

    return PublicError(
        reason="Invalid input.",
        ways_to_solve=tuple(
            f"{error['msg']}: {'.'.join(map(str, error['loc']))}"
            for error in exc.errors()
        ),
    ), status.HTTP_422_UNPROCESSABLE_ENTITY


async def db_conn_handler(
    request: ExtendedRequest, exc: DBConnError
) -> Response:
    """
    Since the DB is an internal and especially sensitive module, the fact that
    it has failed should not be disclosed to the user in order to prevent
    targeted attacks.
    """
    (await request.state.dishka_container.get(Logger)).critical(exc)

    return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@serialize
async def email_conn_handler(
    request: ExtendedRequest, exc: EmailConnError
) -> tuple[PublicError, int]:
    (await request.state.dishka_container.get(Logger)).critical(exc)

    return PublicError(
        reason=exc.user_msg, ways_to_solve=exc.ways_to_solve
    ), status.HTTP_503_SERVICE_UNAVAILABLE


@serialize
async def external_api_conn_handler(
    request: ExtendedRequest, exc: ExternalAPIConnError
) -> tuple[PublicError, int]:
    (await request.state.dishka_container.get(Logger)).exception(exc)

    return PublicError(
        reason=exc.user_msg, ways_to_solve=exc.ways_to_solve
    ), status.HTTP_503_SERVICE_UNAVAILABLE


# If these exceptions were not intercepted in the business layer, then they are
# systemic and are handled accordingly.


async def db_response_handler(
    request: ExtendedRequest, exc: DBResponseError
) -> Response:
    """
    Since the DB is an internal and especially sensitive module, the fact that
    it has failed should not be disclosed to the user in order to prevent
    targeted attacks.
    """
    (await request.state.dishka_container.get(Logger)).exception(exc)

    return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@serialize
async def external_api_response_handler(
    request: ExtendedRequest, exc: ExternalRESTResponseError
) -> tuple[PublicError, int]:
    (await request.state.dishka_container.get(Logger)).exception(exc)

    return PublicError(
        reason=exc.user_msg, ways_to_solve=exc.ways_to_solve
    ), status.HTTP_503_SERVICE_UNAVAILABLE


# These exceptions do not require a body (see the example about HTTP 404 and
# 422 above), but without overriding FastAPI will still add JSON with «detail»
# to them.


async def not_found_handler(
    request: ExtendedRequest, exc: HTTPException
) -> Response:
    (await request.state.dishka_container.get(Logger)).debug(exc)

    return Response(status_code=status.HTTP_404_NOT_FOUND)


async def unexpected_exception_handler(
    request: ExtendedRequest,
    exc: Exception,
) -> Response:
    (await request.state.dishka_container.get(Logger)).critical(exc)

    return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


ExcT_co = TypeVar("ExcT_co", bound=Exception, covariant=True)


def get_handling_map() -> tuple[HandlingPair[Exception], ...]:
    return (
        HandlingPair[DBConnError](exc=DBConnError, handler=db_conn_handler),
        HandlingPair[DBResponseError](
            exc=DBResponseError, handler=db_response_handler
        ),
        HandlingPair[EmailConnError](
            exc=EmailConnError, handler=email_conn_handler
        ),
        HandlingPair[ExternalAPIConnError](
            exc=ExternalAPIConnError, handler=external_api_conn_handler
        ),
        HandlingPair[ExternalRESTResponseError](
            exc=ExternalRESTResponseError,
            handler=external_api_response_handler,
        ),
        HandlingPair[RequestValidationError](
            exc=RequestValidationError,
            handler=validation_handler,
        ),
        HandlingPair[HTTPException](exc=404, handler=not_found_handler),
        HandlingPair[Exception](
            exc=Exception, handler=unexpected_exception_handler
        ),
    )
