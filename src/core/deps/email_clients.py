from collections.abc import AsyncGenerator

from aiosmtplib import SMTP
from dishka import Scope, provide

from src.core.deps.base import BaseProvider
from src.core.settings import EmailSettings
from src.core.utils.email_clients import AIOSMTPLibClient, EmailClient, Session


class AIOSMTPLibProvider(BaseProvider):
    @provide(scope=Scope.REQUEST, provides=Session)
    async def get_session(self, settings: EmailSettings) -> AsyncGenerator[SMTP]:
        async with SMTP(hostname=settings.host, username=settings.user, password=settings.password) as session:
            yield session

    client = provide(source=AIOSMTPLibClient, provides=EmailClient)
