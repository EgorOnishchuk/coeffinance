from collections.abc import AsyncGenerator

from aiosmtplib import SMTP
from dishka import Scope, provide

from src.core.deps.base import CoreProvider
from src.core.infrastructure.mail_sessions import (
    AIOSMTPLibSession,
    MailSession,
)
from src.core.settings import MailCredentials


class AIOSMTPLibProvider(CoreProvider):
    @provide(scope=Scope.REQUEST, provides=MailSession)
    async def get_session(self) -> AsyncGenerator[SMTP]:
        async with AIOSMTPLibSession(
            hostname=MailCredentials.host,
            username=MailCredentials.user,
            password=MailCredentials.password,
            timeout=MailCredentials.timeout,
        ) as session:
            yield session
