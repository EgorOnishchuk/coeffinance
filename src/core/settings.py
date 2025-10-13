from abc import ABC, abstractmethod
from collections.abc import Sequence
from http import HTTPMethod
from typing import Annotated, Self, override

from pydantic import (
    EmailStr,
    Field,
    HttpUrl,
    PositiveFloat,
    PositiveInt,
    field_serializer,
)
from pydantic_core.core_schema import SerializerFunctionWrapHandler
from pydantic_extra_types.semantic_version import SemanticVersion
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.schemas import ENDPOINT, SHA_1, NonEmptyStr


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @classmethod
    def load(cls) -> Self:
        """
        Allows to bypass warnings from linters and type checkers about «missing»
        constructor arguments.
        """
        return cls()


class DBCredentials(Settings):
    schema_: Annotated[NonEmptyStr, Field(validation_alias="db_schema")]
    host: Annotated[NonEmptyStr, Field(validation_alias="db_host")]
    port: Annotated[PositiveInt, Field(validation_alias="db_port")]
    user: Annotated[NonEmptyStr, Field(validation_alias="db_user")]
    password: Annotated[NonEmptyStr, Field(validation_alias="db_password")]
    db_name: NonEmptyStr

    @property
    def dsn(self) -> str:
        return f"{self.schema_}://{self.user}:{self.password}@{self.host}:{self.port}/{self.db_name}"


class DBSettings(Settings):
    size: Annotated[
        PositiveInt,
        Field(validation_alias="db_pool_size"),
    ] = 10
    overflow: Annotated[
        PositiveInt,
        Field(
            validation_alias="db_pool_overflow",
        ),
    ] = 3
    timeout: Annotated[
        PositiveFloat,
        Field(validation_alias="db_timeout"),
    ] = 15
    retries: Annotated[
        PositiveInt,
        Field(validation_alias="db_retries"),
    ] = 5


class ExternalAPISettings(Settings):
    api_fns_token: Annotated[str, Field(pattern=SHA_1)]

    timeout: Annotated[
        PositiveFloat,
        Field(validation_alias="external_api_timeout"),
    ] = 30.0
    retries: Annotated[
        PositiveInt,
        Field(validation_alias="external_api_retries"),
    ] = 3


class MailSettings(Settings):
    host: Annotated[NonEmptyStr, Field(validation_alias="email_host")]
    user: Annotated[NonEmptyStr, Field(validation_alias="email_user")]
    password: Annotated[NonEmptyStr, Field(validation_alias="email_password")]

    timeout: Annotated[
        PositiveFloat, Field(validation_alias="email_timeout")
    ] = 30.0
    retries: Annotated[
        PositiveInt,
        Field(validation_alias="external_api_retries"),
    ] = 3


class CacheCredentials(Settings, ABC):
    """
    It is used selectively and for trivial tasks (sessions, counters, etc.), so
    advanced access rights system is not required: unlike the main dbms, all
    actions are performed on behalf of the default user.
    """

    password: Annotated[NonEmptyStr, Field(validation_alias="cache_password")]
    host: Annotated[NonEmptyStr, Field(validation_alias="cache_host")]

    @property
    @abstractmethod
    def dsn(self) -> str:
        pass


class RedisCredentials(CacheCredentials):
    @property
    @override
    def dsn(self) -> str:
        return f"redis://default:{self.password}@{self.host}"


class AuthSettings(Settings):
    email_verification_secret: NonEmptyStr
    password_reset_secret: NonEmptyStr

    sys_email: EmailStr


class TrustedHostsSettings(Settings):
    hosts: Annotated[
        Sequence[NonEmptyStr] | None, Field(alias="allowed_hosts")
    ] = (
        "localhost",
        "coeffinance.com",
    )


class CORSSettings(Settings):
    allowed_origins: Annotated[
        Sequence[HttpUrl] | None,
        Field(serialization_alias="allow_origins"),
    ] = None
    allowed_origin_regex: Annotated[
        str | None,
        Field(serialization_alias="allow_origin_regex"),
    ] = None
    allowed_methods: Annotated[
        Sequence[HTTPMethod] | None,
        Field(serialization_alias="allow_methods"),
    ] = None
    allowed_headers: Annotated[
        Sequence[NonEmptyStr] | None,
        Field(serialization_alias="allow_headers"),
    ] = None
    are_credentials: Annotated[
        bool | None,
        Field(serialization_alias="allow_credentials"),
    ] = None
    exposed_headers: Annotated[
        Sequence[NonEmptyStr] | None,
        Field(serialization_alias="expose_headers"),
    ] = None
    cache_time: Annotated[
        PositiveInt | None, Field(serialization_alias="max_age")
    ] = None


class CompressionSettings(Settings):
    min_size: Annotated[
        PositiveInt | None,
        Field(serialization_alias="minimum_size"),
    ] = None
    level: Annotated[
        PositiveInt | None,
        Field(serialization_alias="compresslevel", le=9),
    ] = None


class DocsSettings(Settings):
    title: Annotated[NonEmptyStr, Field(max_length=50)]
    summary: Annotated[str | None, Field(min_length=5, max_length=150)] = None
    description: Annotated[str | None, Field(min_length=5, max_length=500)] = (
        None
    )
    version: SemanticVersion
    terms_of_service: HttpUrl | None = None
    contact: dict[str, NonEmptyStr | HttpUrl | EmailStr] | None = None
    license: Annotated[
        dict[str, NonEmptyStr | HttpUrl] | None,
        Field(serialization_alias="license_info"),
    ] = {
        "name": "GNU General Public License v3.0 only",
        "url": "https://www.gnu.org/licenses/gpl-3.0-standalone.html",
    }

    openapi: Annotated[
        str | None,
        Field(serialization_alias="openapi_url", pattern=ENDPOINT),
    ] = None
    docs: Annotated[
        str | None,
        Field(serialization_alias="docs_url", pattern=ENDPOINT),
    ] = None
    redoc: Annotated[
        str | None,
        Field(serialization_alias="redoc_url", pattern=ENDPOINT),
    ] = None

    @field_serializer("version", mode="wrap")
    def serialize_version(
        self, version: SemanticVersion, handler: SerializerFunctionWrapHandler
    ) -> str:
        return str(version)
