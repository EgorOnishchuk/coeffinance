from collections.abc import AsyncGenerator

from aiosmtplib import SMTP
from dishka import Scope, provide

from src.core.deps.base import BaseProvider
from src.core.settings import MailSettings
from src.core.utils.mail import (
    AIOSMTPLibSession,
    MailSession,
)


class AIOSMTPLibProvider(BaseProvider):
    @provide
    def get_mail_settings(self) -> MailSettings:
        return MailSettings.load()

    @provide(scope=Scope.REQUEST, provides=MailSession)
    async def get_session(self, settings: MailSettings) -> AsyncGenerator[SMTP]:
        async with AIOSMTPLibSession(
            settings=settings,
        ) as session:
            yield session
