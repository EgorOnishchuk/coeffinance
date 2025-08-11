from abc import ABC, abstractmethod
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Generic, TypeVar

from aiosmtplib import SMTP, SMTPException

from src.core.errors import EmailConnError
from src.core.settings import EmailSettings

Session = SMTP
SessionT = TypeVar("SessionT", bound=Session)


@dataclass(kw_only=True, slots=True, frozen=True)
class EmailClient(ABC, Generic[SessionT]):
    _settings: EmailSettings

    @staticmethod
    def _prepare(sender: str, recipient: str, title: str, text: str) -> EmailMessage:
        message = EmailMessage()

        message["From"], message["To"], message["Subject"] = sender, recipient, title
        message.set_content(text)

        return message

    @abstractmethod
    async def send(self, session: SessionT, sender: str, recipient: str, title: str, text: str) -> None:
        raise NotImplementedError


class AIOSMTPLibClient(EmailClient[SMTP]):
    async def send(self, session: SMTP, sender: str, recipient: str, title: str, text: str) -> None:
        message = self._prepare(sender, recipient, title, text)

        try:
            await session.send_message(message, timeout=self._settings.timeout)
        except SMTPException as exc:
            raise EmailConnError from exc
