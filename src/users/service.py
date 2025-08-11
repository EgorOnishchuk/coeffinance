from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dishka import AsyncContainer
from fastapi import Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users import BaseUserManager, IntegerIDMixin
from fastapi_users.db import BaseUserDatabase
from fastapi_users.exceptions import InvalidResetPasswordToken as LibInvalidResetPasswordToken
from fastapi_users.exceptions import InvalidVerifyToken as LibInvalidVerifyToken
from fastapi_users.exceptions import UserAlreadyExists as LibUserAlreadyExists
from fastapi_users.exceptions import UserAlreadyVerified as LibUserAlreadyVerified
from fastapi_users.exceptions import UserInactive as LibUserInactive
from fastapi_users.exceptions import UserNotExists as LibUserNotExists
from fastapi_users.password import PasswordHelperProtocol

from src.core.settings import AuthSettings
from src.core.utils.email_clients import EmailClient, Session
from src.users.errors import (
    AlreadyExistsError,
    AlreadyVerifiedError,
    AuthenticationError,
    PasswordResetError,
    UnverifiedError,
    VerificationError,
    WeakPasswordError,
)
from src.users.models import SQLAlchemyUser
from src.users.schemas import UserCreate, UserUpdate
from src.users.utils.utils import PasswordValidator


class SQLAlchemyUserManager(IntegerIDMixin, BaseUserManager[SQLAlchemyUser, int]):  # type: ignore[type-var]
    """
    Also overrides exception classes via their interception.
    """

    def __init__(
        self,
        user_db: BaseUserDatabase[SQLAlchemyUser, int],  # type: ignore[type-var]
        settings: AuthSettings,
        email_client: EmailClient,
        password_validator: PasswordValidator,
        password_helper: PasswordHelperProtocol | None = None,
    ) -> None:
        super().__init__(user_db, password_helper)

        self.settings = settings
        self.verification_token_secret, self.reset_password_token_secret = (
            self.settings.email_verification_secret,
            self.settings.password_reset_secret,
        )
        self.email_client = email_client
        self.password_validator = password_validator

    async def validate_password(
        self,
        password: str,
        user: UserCreate | SQLAlchemyUser,  # type: ignore[override]
    ) -> None:
        if not self.password_validator.is_strong(password, related=(user.email, user.nickname)):
            raise WeakPasswordError(ways_to_solve=self.password_validator.get_improvements(password))

    async def on_after_request_verify(  # type: ignore[override]
        self, user: SQLAlchemyUser, token: str, request: Request
    ) -> None:
        container: AsyncContainer = request.app.state.dishka_container

        async with container() as sub_container:
            await self.email_client.send(
                session=await sub_container.get(Session),
                sender=self.settings.sys_email,
                recipient=user.email,
                title="Email confirmation",
                text=f"Please confirm your email address with this code: {token}",
            )

    async def on_after_forgot_password(  # type: ignore[override]
        self, user: SQLAlchemyUser, token: str, request: Request
    ) -> None:
        container: AsyncContainer = request.app.state.dishka_container

        async with container() as sub_container:
            await self.email_client.send(
                session=await sub_container.get(Session),
                sender=self.settings.sys_email,
                recipient=user.email,
                title="Password reset",
                text=f"Please reset your password with this code: {token}",
            )

    async def create(
        self,
        user_create: UserCreate,  # type: ignore[override]
        safe: bool = False,  # noqa: FBT001, FBT002
        request: Request | None = None,
    ) -> SQLAlchemyUser:
        try:
            return await super().create(user_create, safe, request)
        except LibUserAlreadyExists as exc:
            raise AlreadyExistsError from exc

    async def update(  # type: ignore[override]
        self,
        user_update: UserUpdate,
        user: SQLAlchemyUser,
        request: Request,
        safe: bool = False,  # noqa: FBT001, FBT002
    ) -> SQLAlchemyUser:
        try:
            return await super().update(user_update, user, safe, request)
        except LibUserAlreadyExists as exc:
            raise AlreadyExistsError from exc

    async def authenticate(self, credentials: OAuth2PasswordRequestForm) -> SQLAlchemyUser | None:
        user = await super().authenticate(credentials)

        if user is None or not user.is_active:
            raise AuthenticationError

        if not user.is_verified:
            raise UnverifiedError

        return user

    async def verify(self, token: str, request: Request) -> SQLAlchemyUser:  # type: ignore[override]
        try:
            return await super().verify(token, request)
        except (LibInvalidVerifyToken, LibUserNotExists) as exc:
            raise VerificationError from exc
        except LibUserAlreadyVerified as exc:
            raise AlreadyVerifiedError from exc

    async def reset_password(  # type: ignore[override]
        self, token: str, password: str, request: Request
    ) -> SQLAlchemyUser:
        try:
            return await super().reset_password(token, password, request)
        except (
            LibInvalidResetPasswordToken,
            LibUserNotExists,
            LibUserInactive,
        ) as exc:
            raise PasswordResetError from exc
