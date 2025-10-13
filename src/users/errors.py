from fastapi import HTTPException, Response, status

from src.core.asgi import ExtendedRequest, HandlingPair
from src.core.errors import (
    DetailedError,
    serialize,
)
from src.core.schemas import PublicError
from src.core.utils.loggers import Logger


class WeakPasswordError(DetailedError):
    def __init__(
        self,
        msg: str = "Password is weak.",
        ways_to_solve: tuple[str, ...] = (
            "Make up a more complex password.",
            "Consider using a software-generated password.",
        ),
    ) -> None:
        super().__init__(msg, user_msg=msg, ways_to_solve=ways_to_solve)


class AlreadyExistsError(DetailedError):
    def __init__(
        self,
        msg: str = "User already exists.",
        ways_to_solve: tuple[str, ...] = (
            "Make sure your email is valid and is not compromised, blocked or "
            "deleted.",
            "Try logging in.",
        ),
    ) -> None:
        super().__init__(msg, user_msg=msg, ways_to_solve=ways_to_solve)


class AuthenticationError(DetailedError):
    def __init__(
        self,
        msg: str = "Invalid credentials or status.",
        ways_to_solve: tuple[str, ...] = (
            "Make sure your email and password are valid.",
            "Make sure your account exists and is not deactivated.",
        ),
    ) -> None:
        super().__init__(msg, user_msg=msg, ways_to_solve=ways_to_solve)


class UnverifiedError(DetailedError):
    def __init__(
        self,
        msg: str = "Email is not verified.",
        ways_to_solve: tuple[str, ...] = ("Please, verify your email.",),
    ) -> None:
        super().__init__(msg, user_msg=msg, ways_to_solve=ways_to_solve)


class VerificationError(DetailedError):
    def __init__(
        self,
        msg: str = "Invalid verification code or status.",
        ways_to_solve: tuple[str, ...] = (
            "Make sure your inbox address and code are valid.",
            "Make sure your email and password are valid.",
            "Make sure your account exists and is not deactivated.",
        ),
    ) -> None:
        super().__init__(msg, user_msg=msg, ways_to_solve=ways_to_solve)


class AlreadyVerifiedError(DetailedError):
    def __init__(
        self,
        msg: str = "Email is already verified.",
        ways_to_solve: tuple[str, ...] = (
            "Make sure your email is valid.",
            "Try logging in instead of verifying.",
        ),
    ) -> None:
        super().__init__(msg, user_msg=msg, ways_to_solve=ways_to_solve)


class PasswordResetError(DetailedError):
    def __init__(
        self,
        msg: str = "Invalid or expired reset code or status.",
        ways_to_solve: tuple[str, ...] = (
            "Make sure your inbox address is valid.",
            "Make sure your code is valid and is not expired.",
            "Make sure your account exists and is not deactivated.",
        ),
    ) -> None:
        super().__init__(msg, user_msg=msg, ways_to_solve=ways_to_solve)


@serialize
async def weak_password_handler(
    request: ExtendedRequest, exc: WeakPasswordError
) -> tuple[PublicError, int]:
    (await request.state.dishka_container.get(Logger)).debug(exc)

    return PublicError(
        reason=exc.user_msg, ways_to_solve=exc.ways_to_solve
    ), status.HTTP_400_BAD_REQUEST


@serialize
async def authentication_handler(
    request: ExtendedRequest, exc: AuthenticationError
) -> tuple[PublicError, int]:
    (await request.state.dishka_container.get(Logger)).debug(exc)

    return PublicError(
        reason=exc.user_msg, ways_to_solve=exc.ways_to_solve
    ), status.HTTP_400_BAD_REQUEST


@serialize
async def unverified_handler(
    request: ExtendedRequest, exc: UnverifiedError
) -> tuple[PublicError, int]:
    (await request.state.dishka_container.get(Logger)).debug(exc)

    return PublicError(
        reason=exc.user_msg, ways_to_solve=exc.ways_to_solve
    ), status.HTTP_400_BAD_REQUEST


@serialize
async def verification_handler(
    request: ExtendedRequest, exc: VerificationError
) -> tuple[PublicError, int]:
    (await request.state.dishka_container.get(Logger)).debug(exc)

    return PublicError(
        reason=exc.user_msg, ways_to_solve=exc.ways_to_solve
    ), status.HTTP_400_BAD_REQUEST


@serialize
async def already_verified_handler(
    request: ExtendedRequest, exc: AlreadyVerifiedError
) -> tuple[PublicError, int]:
    (await request.state.dishka_container.get(Logger)).debug(exc)

    return PublicError(
        reason=exc.user_msg, ways_to_solve=exc.ways_to_solve
    ), status.HTTP_400_BAD_REQUEST


@serialize
async def password_reset_handler(
    request: ExtendedRequest, exc: PasswordResetError
) -> tuple[PublicError, int]:
    (await request.state.dishka_container.get(Logger)).debug(exc)

    return PublicError(
        reason=exc.user_msg, ways_to_solve=exc.ways_to_solve
    ), status.HTTP_400_BAD_REQUEST


# These exceptions do not require a body (see core/errors.py for details).


async def unauthenticated_handler(
    request: ExtendedRequest, exc: HTTPException
) -> Response:
    (await request.state.dishka_container.get(Logger)).debug(exc)

    return Response(status_code=status.HTTP_401_UNAUTHORIZED)


async def unauthorized_handler(
    request: ExtendedRequest, exc: HTTPException
) -> Response:
    (await request.state.dishka_container.get(Logger)).exception(exc)

    return Response(status_code=status.HTTP_403_FORBIDDEN)


def get_user_handling_map() -> tuple[HandlingPair[Exception], ...]:
    return (
        HandlingPair[WeakPasswordError](
            exc=WeakPasswordError, handler=weak_password_handler
        ),
        HandlingPair[AuthenticationError](
            exc=AuthenticationError, handler=authentication_handler
        ),
        HandlingPair[UnverifiedError](
            exc=UnverifiedError, handler=unverified_handler
        ),
        HandlingPair[VerificationError](
            exc=VerificationError, handler=verification_handler
        ),
        HandlingPair[AlreadyVerifiedError](
            exc=AlreadyVerifiedError, handler=already_verified_handler
        ),
        HandlingPair[PasswordResetError](
            exc=PasswordResetError, handler=password_reset_handler
        ),
        HandlingPair[HTTPException](exc=401, handler=unauthenticated_handler),
        HandlingPair[HTTPException](exc=403, handler=unauthorized_handler),
    )
