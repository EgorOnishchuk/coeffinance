from __future__ import annotations

import sys
from collections.abc import (
    Awaitable,
    Callable,
    Mapping,
)
from functools import wraps
from logging import CRITICAL, DEBUG, ERROR
from types import TracebackType
from typing import ClassVar, Final

from fastapi import Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status
from starlette.status import (
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from src.core.asgi import HTTPStatus
from src.core.infrastructure.api_sessions import JSON
from src.core.utils.logging import Level, logger
from src.core.validators import PublicError


def core_exc_handlers() -> dict[
    type[Exception] | HTTPStatus,
    Callable[[Exception], Awaitable[Response]],
]:
    internal_error_handler = nondetailed_handler(
        HTTP_500_INTERNAL_SERVER_ERROR,
    )
    resource_not_found_handler = nondetailed_handler(
        HTTP_404_NOT_FOUND,
    )
    obj_not_found_handler = detailed_handler(
        HTTP_404_NOT_FOUND,
    )
    already_exists_handler = nondetailed_handler(
        HTTP_409_CONFLICT,
    )

    sys_handlers = {
        DBConnError: internal_error_handler,
        DBResponseError: internal_error_handler,
        ExternalAPIConnError: internal_error_handler,
        ExternalAPIResponseError: internal_error_handler,
        MailConnError: internal_error_handler,
        MailResponseError: internal_error_handler,
        # Responses below do not require a body (see the examples about 401 and
        # 403 above), but without overriding FastAPI will still add JSON
        # with «detail» to them.
        HTTP_404_NOT_FOUND: resource_not_found_handler,
        Exception: internal_error_handler,
    }
    business_handlers = {
        NotFoundError: obj_not_found_handler,
        AlreadyExistsError: already_exists_handler,
    }

    return {**sys_handlers, **business_handlers}


def nondetailed_handler(
    code: HTTPStatus,
) -> Callable[[CoreError], Awaitable[Response]]:
    """
    When the meaning of a business error is clear at the protocol level
    (401 Unauthorized, 403 Forbidden, etc.) or an error is systemic and
    therefore should not be exposed (500 Internal Server Error, etc.).
    """

    async def handler(
        exc: CoreError,
    ) -> Response:
        return Response(status_code=code)

    return handler


def detailed_handler(
    code: HTTPStatus,
) -> Callable[[BusinessError], Awaitable[JSONResponse]]:
    """
    When the meaning of a business error is unclear at the protocol level and
    additional context needs to be provided (400 Bad Request, 422 Unprocessable
    Entity, etc.).
    """

    async def handler(
        exc: BusinessError,
    ) -> JSONResponse:
        return JSONResponse(
            content=PublicError(type=exc.type, details=exc.details).model_dump(
                mode="json",
                exclude_none=True,
            ),
            status_code=code,
        )

    return handler


async def validation_handler(
    exc: RequestValidationError,
) -> JSONResponse:
    details = {error['msg']: '.'.join(error['loc']) for error in exc.errors()}

    return JSONResponse(
        content=PublicError(type=type(exc).__name__, details=details).model_dump(
            mode="json",
            exclude_none=True,
        ),
        status_code=status.,
    )


def serialize[**P](
    func: Callable[P, Awaitable[tuple[PublicError, HTTPStatus]]],
) -> Callable[P, Awaitable[JSONResponse]]:
    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> JSONResponse:
        error, code = await func(*args, **kwargs)


    return wrapper


class CoreError(Exception):
    default_log_level: ClassVar[Level] = DEBUG

    def __init__(
        self,
        *args,
        log_level: Level | None = None,
        details: Mapping[str, JSON] | None = None,
    ) -> None:
        super().__init__(*args)

        self.log_level: Final = (
            log_level if log_level is not None else self.default_log_level
        )
        self.details: Final = details if details is not None else {}

    @property
    def type(self) -> str:
        return type(self).__name__

    @property
    def original(self) -> BaseException | None:
        return self.__cause__ or self.__context__


class SysError(CoreError):
    default_log_level = ERROR


class DBConnError(SysError, ConnectionError):
    default_log_level = CRITICAL


class DBResponseError(SysError):
    default_log_level = CRITICAL


class ExternalAPIConnError(SysError, ConnectionError):
    pass


class ExternalAPIResponseError(SysError):
    pass


class MailConnError(SysError, ConnectionError):
    pass


class MailResponseError(SysError):
    pass


class BusinessError(CoreError):
    pass


class NotFoundError(BusinessError):
    pass


class AlreadyExistsError(BusinessError):
    pass


def sys_handler(
    type_: type[BaseException],
    value: BaseException,
    traceback: TracebackType,
) -> None:
    if isinstance(value, KeyboardInterrupt):
        sys.__excepthook__(type_, value, traceback)
        return

    if isinstance(value, CoreError):
        logger().log(level=value.log_level, event=value.type, **value.details)

    logger().critical(type_.__name__, exc_info=(type_, value, traceback))
