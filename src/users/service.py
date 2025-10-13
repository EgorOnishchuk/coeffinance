from typing import cast, override

from fastapi import HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users import BaseUserManager, IntegerIDMixin
from fastapi_users.db import BaseUserDatabase
from fastapi_users.exceptions import (
    InvalidResetPasswordToken as LibInvalidResetPasswordToken,
)
from fastapi_users.exceptions import InvalidVerifyToken as LibInvalidVerifyToken
from fastapi_users.exceptions import UserAlreadyExists as LibUserAlreadyExists
from fastapi_users.exceptions import (
    UserAlreadyVerified as LibUserAlreadyVerified,
)
from fastapi_users.exceptions import UserInactive as LibUserInactive
from fastapi_users.exceptions import UserNotExists as LibUserNotExists
from fastapi_users.password import PasswordHelperProtocol
from fastapi_users.schemas import BaseUserCreate, BaseUserUpdate

from src.core.asgi import ExtendedRequest
from src.core.settings import AuthSettings
from src.core.utils.mail import MailSession
from src.users.db.models import DBUserProtocol
from src.users.errors import (
    AlreadyExistsError,
    AlreadyVerifiedError,
    AuthenticationError,
    PasswordResetError,
    UnverifiedError,
    VerificationError,
    WeakPasswordError,
)
from src.users.schemas import UserCreate
from src.users.utils.password_validators import PasswordValidator


class UserManager(IntegerIDMixin, BaseUserManager[DBUserProtocol, int]):
    """
    Also overrides exception classes via their interception.
    """

    def __init__(
        self,
        user_db: BaseUserDatabase[DBUserProtocol, int],
        settings: AuthSettings,
        password_validator: PasswordValidator,
        password_helper: PasswordHelperProtocol | None = None,
    ) -> None:
        super().__init__(user_db, password_helper)

        self._settings = settings
        self.verification_token_secret, self.reset_password_token_secret = (
            self._settings.email_verification_secret,
            self._settings.password_reset_secret,
        )
        self._password_validator = password_validator

    @override
    async def validate_password(
        self,
        password: str,
        user: BaseUserCreate | DBUserProtocol,
    ) -> None:
        # A generic for the user creation schema is not provided by the lib,
        # but BaseUserCreate is UserCreate here, since it is assigned at the
        # moment of obtaining APIRouter.
        # (see «fastapi_users.get_register_router(UserRead, UserCreate)» in
        # routes.py)
        user = cast(UserCreate | DBUserProtocol, user)
        report = self._password_validator.validate(
            password,
            related=(user.nickname, user.email),
        )

        if not report.is_strong:
            raise WeakPasswordError(
                f"Password is not enough strong: {report.strength}.",
                ways_to_solve=tuple(report.improvements),
            )

    @override
    async def on_after_request_verify(
        self,
        user: DBUserProtocol,
        token: str,
        request: Request | None = None,
    ) -> None:
        if request is None:
            raise HTTPException(status_code=500)
        request = cast(ExtendedRequest, request)

        async with request.app.state.dishka_container() as sub_container:
            await (await sub_container.get(MailSession)).send(
                sender=str(self._settings.sys_email),
                recipient=user.email,
                title="Email confirmation",
                text=f"Please confirm your email address with this code: "
                f"{token}",
            )

    @override
    async def on_after_forgot_password(
        self,
        user: DBUserProtocol,
        token: str,
        request: Request | None = None,
    ) -> None:
        if request is None:
            raise HTTPException(status_code=500)
        request = cast(ExtendedRequest, request)

        async with request.app.state.dishka_container() as sub_container:
            await (await sub_container.get(MailSession)).send(
                sender=str(self._settings.sys_email),
                recipient=user.email,
                title="Password reset",
                text=f"Please reset your password with this code: {token}",
            )

    @override
    async def create(
        self,
        user_create: BaseUserCreate,
        safe: bool = False,
        request: Request | None = None,
    ) -> DBUserProtocol:
        if request is None:
            raise HTTPException(status_code=500)

        try:
            return await super().create(user_create, safe, request)
        except LibUserAlreadyExists as exc:
            raise AlreadyExistsError from exc

    @override
    async def update(
        self,
        user_update: BaseUserUpdate,
        user: DBUserProtocol,
        safe: bool = False,
        request: Request | None = None,
    ) -> DBUserProtocol:
        if request is None:
            raise HTTPException(status_code=500)

        try:
            return await super().update(user_update, user, safe, request)
        except LibUserAlreadyExists as exc:
            raise AlreadyExistsError from exc

    @override
    async def authenticate(
        self, credentials: OAuth2PasswordRequestForm
    ) -> DBUserProtocol | None:
        user = await super().authenticate(credentials)

        if user is None or not user.is_active:
            raise AuthenticationError

        if not user.is_verified:
            raise UnverifiedError

        return user

    @override
    async def verify(
        self, token: str, request: Request | None = None
    ) -> DBUserProtocol:
        try:
            return await super().verify(token, request)
        except (LibInvalidVerifyToken, LibUserNotExists) as exc:
            raise VerificationError from exc
        except LibUserAlreadyVerified as exc:
            raise AlreadyVerifiedError from exc

    @override
    async def reset_password(
        self,
        token: str,
        password: str,
        request: Request | None = None,
    ) -> DBUserProtocol:
        try:
            return await super().reset_password(token, password, request)
        except (
            LibInvalidResetPasswordToken,
            LibUserNotExists,
            LibUserInactive,
        ) as exc:
            raise PasswordResetError from exc
