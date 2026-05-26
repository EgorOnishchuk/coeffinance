from collections.abc import Iterable, Sequence
from email.message import EmailMessage, Message
from typing import (
    ClassVar,
    Literal,
    Protocol,
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
from aiosmtplib.typing import Default
from structlog.contextvars import bind_contextvars
from tenacity import retry, retry_if_exception_type, stop_after_attempt

from src.core.errors import MailConnError, MailResponseError
from src.core.settings import MailCredentials
from src.core.utils.logging import MailRequestLog, MailResponseLog


class MailSession(Protocol):
    async def send_plain(
        self,
        sender: str,
        recipients: str | Sequence[str],
        *,
        title: str,
        text: str,
    ) -> None: ...


class AIOSMTPLibSession(SMTP):
    ConnErrors: ClassVar = (
        SMTPServerDisconnected,
        SMTPConnectError,
        SMTPTimeoutError,
    )

    @staticmethod
    def _prepare(
        sender: str, recipients: str | Sequence[str], *, title: str, text: str
    ) -> EmailMessage:
        message = EmailMessage()

        message["From"], message["To"], message["Subject"] = (
            sender,
            ", ".join(recipients),
            title,
        )
        message.set_content(text)

        return message

    @retry(
        retry=retry_if_exception_type(MailConnError),
        stop=stop_after_attempt(MailCredentials().retries),
        reraise=True,
    )
    @override
    async def send_message(
        self,
        message: EmailMessage | Message,
        /,
        *,
        sender: str | None = None,
        recipients: str | Sequence[str] | None = None,
        mail_options: Iterable[str] | None = None,
        rcpt_options: Iterable[str] | None = None,
        timeout: float | Literal[Default.token] | None = Default.token,
    ) -> tuple[dict[str, SMTPResponse], str]:
        request_log = MailRequestLog(
            sender=sender,
            recipients=recipients,
            title=message["title"],
            text=message["text"],
        )

        try:
            return await super().send_message(
                message,
                sender=sender,
                recipients=recipients,
                mail_options=mail_options,
                rcpt_options=rcpt_options,
                timeout=timeout,
            )
        except self.ConnErrors as exc:
            bind_contextvars(
                **dict(request_log),
            )
            raise MailConnError from exc
        except SMTPResponseException as exc:
            bind_contextvars(
                **dict(request_log),
                **dict(
                    MailResponseLog(
                        code=exc.code,
                        msg=exc.message,
                    )
                ),
            )
            raise MailResponseError from exc

    async def send_plain(
        self,
        sender: str,
        recipients: str | Sequence[str],
        *,
        title: str,
        text: str,
    ) -> None:
        await self.send_message(
            self._prepare(
                sender,
                recipients,
                title=title,
                text=text,
            ),
        )
