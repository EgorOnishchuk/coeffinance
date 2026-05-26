from collections.abc import Iterator, Mapping, Sequence
from contextvars import Token
from dataclasses import asdict, dataclass
from logging import basicConfig
from typing import Any, ClassVar, Literal, Self

import structlog
from httpx import URL
from httpx._types import HeaderTypes, QueryParamTypes
from structlog.contextvars import bind_contextvars, merge_contextvars
from structlog.dev import ConsoleRenderer
from structlog.processors import (
    EventRenamer,
    JSONRenderer,
    TimeStamper,
    add_log_level,
    dict_tracebacks,
)
from structlog.stdlib import BoundLogger, LoggerFactory, filter_by_level

from src.core.infrastructure.api_sessions import (
    JSON,
)
from src.core.infrastructure.db_models import SQLAlchemyModel
from src.core.settings import LoggingSettings

logger = structlog.stdlib.get_logger

type Level = Literal[
    10,
    20,
    30,
    40,
    50,
]


@dataclass(kw_only=True, slots=True)
class Log:
    namespace: ClassVar

    def __iter__(self) -> Iterator[tuple[str, dict[str, Any]]]:
        yield self.namespace, asdict(self)


@dataclass(kw_only=True, slots=True)
class IncomingHTTPRequestLog(Log):
    namespace = "incoming_request"

    id: str
    client_host: str
    client_port: int
    path: str

    version: str
    method: str
    path_params: Mapping[str, str] | None = None
    query_params: Mapping[str, str] | None = None
    headers: Mapping[str, str] | None = None


@dataclass(kw_only=True, slots=True)
class OutgoingHTTPRequestLog(Log):
    namespace = "outgoing_request"

    scheme: str
    host: str
    port: int | None = None
    path: str

    method: str
    headers: HeaderTypes | None = None
    query_params: QueryParamTypes | None = None

    @classmethod
    def from_url(
        cls,
        url: URL,
        *,
        method: str,
        headers: HeaderTypes,
        params: QueryParamTypes,
    ) -> Self:
        return cls(
            scheme=url.scheme,
            host=url.host,
            port=url.port,
            path=url.path,
            method=method,
            headers=headers,
            query_params=params,
        )


@dataclass(kw_only=True, slots=True)
class IncomingHTTPResponseLog(Log):
    namespace = "incoming_response"

    code: int
    headers: HeaderTypes | None = None


@dataclass(kw_only=True, slots=True)
class RESTLog(Log):
    namespace = "rest"

    request_body: JSON | None = None
    response_body: JSON | None = None


@dataclass(kw_only=True, slots=True)
class MailRequestLog(Log):
    namespace = "mail_request"

    sender: str
    recipients: str | Sequence[str]

    title: str
    text: str


@dataclass(kw_only=True, slots=True)
class MailResponseLog(Log):
    namespace = "mail_response"

    code: int
    msg: str


@dataclass(kw_only=True, slots=True)
class SQLLog(Log):
    namespace = "sql"

    statement: str
    params: Mapping[str, Any] | None = None


@dataclass(kw_only=True, slots=True)
class SQLAlchemyLog(Log):
    namespace = "orm"

    objects: Sequence[SQLAlchemyModel]


def bind(*logs: Log) -> Mapping[str, Token]:
    return bind_contextvars(
        **{namespace: context for log in logs for namespace, context in log}
    )


def setup():
    basicConfig(
        format="%(message)s",
        level=LoggingSettings().level,
    )

    structlog.configure(
        processors=(
            merge_contextvars,
            filter_by_level,
            add_log_level,
            TimeStamper(fmt="iso"),
            EventRenamer("type"),
            dict_tracebacks,
            JSONRenderer() if LoggingSettings().is_json else ConsoleRenderer(),
        ),
        wrapper_class=BoundLogger,
        logger_factory=LoggerFactory(),
    )
