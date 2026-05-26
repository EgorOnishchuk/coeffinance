from collections.abc import Awaitable, Callable

from fastapi import Response

from src.core.asgi import HTTPStatus, TypedRequest, WSStatus
from src.core.errors import (
    DetailedError,
    detailed_handler,
    nondetailed_handler,
)


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


def get_user_handling_map() -> tuple[
    tuple[
        Exception | HTTPStatus | WSStatus,
        Callable[[TypedRequest, Exception], Awaitable[Response]],
    ],
    ...,
]:
    bad_request_handler = detailed_handler(
        HTTPStatus.HTTP_400_BAD_REQUEST,
    )

    return (
        (WeakPasswordError, bad_request_handler),
        (AlreadyExistsError, bad_request_handler),
        (AuthenticationError, bad_request_handler),
        (UnverifiedError, bad_request_handler),
        (VerificationError, bad_request_handler),
        (AlreadyVerifiedError, bad_request_handler),
        (PasswordResetError, bad_request_handler),
        (
            HTTPStatus.HTTP_403_FORBIDDEN,
            nondetailed_handler(
                HTTPStatus.HTTP_403_FORBIDDEN,
                "warning",
            ),
        ),
    )
