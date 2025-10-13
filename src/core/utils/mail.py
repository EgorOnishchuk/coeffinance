from abc import ABC, abstractmethod
from dataclasses import dataclass
from email.message import EmailMessage, Message
from typing import (
    Any,
    Final,
    override,
)

from aiosmtplib import (
    SMTP,
    SMTPConnectError,
    SMTPResponse,
    SMTPResponseException,
    SMTPServerDisconnected,
    SMTPTimeoutError,
)
from tenacity import retry, retry_if_exception_type, stop_after_attempt

from src.core.errors import EmailConnError, EmailResponseError
from src.core.settings import MailSettings


@dataclass(kw_only=True, slots=True)
class MailSession(ABC):
    _settings: Final[MailSettings]  # type: ignore[misc] # A MyPy limitation when dealing with dataclasses with Final, not confirmed by Pyright: https://github.com/python/mypy/issues/5608.

    @staticmethod
    def _prepare(
        *, sender: str, recipient: str, title: str, text: str
    ) -> EmailMessage:
        message = EmailMessage()

        message["From"], message["To"], message["Subject"] = (
            sender,
            recipient,
            title,
        )
        message.set_content(text)

        return message

    @abstractmethod
    async def send(
        self,
        *,
        sender: str,
        recipient: str,
        title: str,
        text: str,
        **kwargs: Any,
    ) -> None:
        raise NotImplementedError


class AIOSMTPLibSession(SMTP, MailSession):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(
            *args,
            hostname=self._settings.host,
            username=self._settings.user,
            password=self._settings.password,
            timeout=self._settings.timeout,
            **kwargs,
        )

        self.send_message = retry(  # type: ignore[method-assign] # An alternative to the «sugar» decorator syntax for top-level methods (self cannot be used there, since the instance has not already been created).
            retry=retry_if_exception_type(
                (
                    SMTPServerDisconnected,
                    SMTPConnectError,
                    SMTPTimeoutError,
                )
            ),
            stop=stop_after_attempt(self._settings.retries),
            reraise=True,
        )(self.send_message)

    @override
    async def send_message(
        self,
        message: EmailMessage | Message,
        *args: Any,
        **kwargs: Any,
    ) -> tuple[dict[str, SMTPResponse], str]:
        try:
            return await super().send_message(message, *args, **kwargs)
        except (
            SMTPServerDisconnected,
            SMTPConnectError,
            SMTPTimeoutError,
        ) as exc:
            raise EmailConnError(exc.message) from exc
        except SMTPResponseException as exc:
            raise EmailResponseError(exc.message, code=exc.code) from exc

    @override
    async def send(
        self,
        *,
        sender: str,
        recipient: str,
        title: str,
        text: str,
        **kwargs: Any,
    ) -> None:
        await self.send_message(
            self._prepare(
                sender=sender,
                recipient=recipient,
                title=title,
                text=text,
            ),
            **kwargs,
        )
