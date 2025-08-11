from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dishka import AsyncContainer
from fastapi import Request, status

from src.core.errors import DetailedError, serialize
from src.core.schemas import Error
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
        super().__init__(msg, ways_to_solve)


class AlreadyExistsError(DetailedError):
    def __init__(
        self,
        msg: str = "User is already registered.",
        ways_to_solve: tuple[str, ...] = (
            "Make sure your email is valid and is not compromised, blocked or deleted.",
            "Try logging in.",
        ),
    ) -> None:
        super().__init__(msg, ways_to_solve)


class AuthenticationError(DetailedError):
    def __init__(
        self,
        msg: str = "Invalid credentials or status.",
        ways_to_solve: tuple[str, ...] = (
            "Make sure your email and password are valid.",
            "Make sure your account exists and is not deactivated.",
        ),
    ) -> None:
        super().__init__(msg, ways_to_solve)


class UnverifiedError(DetailedError):
    def __init__(
        self, msg: str = "Email is not verified.", ways_to_solve: tuple[str, ...] = ("Please, verify your email.",)
    ) -> None:
        super().__init__(msg, ways_to_solve)


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
        super().__init__(msg, ways_to_solve)


class AlreadyVerifiedError(DetailedError):
    def __init__(
        self,
        msg: str = "Email is already verified.",
        ways_to_solve: tuple[str, ...] = ("Make sure your email is valid.", "Try logging in instead of verifying."),
    ) -> None:
        super().__init__(msg, ways_to_solve)


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
        super().__init__(msg, ways_to_solve)


@serialize
async def weak_password_handler(request: Request, exc: WeakPasswordError) -> tuple[Error, int]:
    container: AsyncContainer = request.app.state.dishka_container
    (await container.get(Logger)).debug(exc)

    return Error(reason=exc.args[0], ways_to_solve=exc.ways_to_solve), status.HTTP_400_BAD_REQUEST


@serialize
async def already_exists_handler(request: Request, exc: AlreadyExistsError) -> tuple[Error, int]:
    container: AsyncContainer = request.app.state.dishka_container
    (await container.get(Logger)).debug(exc)

    return Error(reason=exc.args[0], ways_to_solve=exc.ways_to_solve), status.HTTP_400_BAD_REQUEST


@serialize
async def authentication_handler(request: Request, exc: AuthenticationError) -> tuple[Error, int]:
    container: AsyncContainer = request.app.state.dishka_container
    (await container.get(Logger)).debug(exc)

    return Error(reason=exc.args[0], ways_to_solve=exc.ways_to_solve), status.HTTP_400_BAD_REQUEST


@serialize
async def unverified_handler(request: Request, exc: UnverifiedError) -> tuple[Error, int]:
    container: AsyncContainer = request.app.state.dishka_container
    (await container.get(Logger)).debug(exc)

    return Error(reason=exc.args[0], ways_to_solve=exc.ways_to_solve), status.HTTP_400_BAD_REQUEST


@serialize
async def verification_handler(request: Request, exc: VerificationError) -> tuple[Error, int]:
    container: AsyncContainer = request.app.state.dishka_container
    (await container.get(Logger)).debug(exc)

    return Error(reason=exc.args[0], ways_to_solve=exc.ways_to_solve), status.HTTP_400_BAD_REQUEST


@serialize
async def already_verified_handler(request: Request, exc: AlreadyVerifiedError) -> tuple[Error, int]:
    container: AsyncContainer = request.app.state.dishka_container
    (await container.get(Logger)).debug(exc)

    return Error(reason=exc.args[0], ways_to_solve=exc.ways_to_solve), status.HTTP_400_BAD_REQUEST


@serialize
async def password_reset_handler(request: Request, exc: PasswordResetError) -> tuple[Error, int]:
    container: AsyncContainer = request.app.state.dishka_container
    (await container.get(Logger)).debug(exc)

    return Error(reason=exc.args[0], ways_to_solve=exc.ways_to_solve), status.HTTP_400_BAD_REQUEST
