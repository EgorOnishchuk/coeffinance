from collections.abc import Mapping, Sequence
from http import HTTPMethod
from typing import Annotated

from pydantic import (
    EmailStr,
    Field,
    HttpUrl,
    NonNegativeInt,
    PositiveFloat,
    PositiveInt,
)
from pydantic_extra_types.semantic_version import SemanticVersion
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.infrastructure.api_sessions import HTTPMethod
from src.core.utils.logging import Level
from src.core.validators import NonEmptyStr


class CoreSettings(BaseSettings):
    pass


class URL(CoreSettings):
    scheme: NonEmptyStr
    host: NonEmptyStr
    username: NonEmptyStr | None = None
    password: NonEmptyStr | None = None
    port: NonNegativeInt | None = None
    path: str
    query: Mapping[str, str] = {}

    def __str__(self) -> str:
        return (
            f"{self.scheme}://{self.username}:{self.password}@"
            f"{self.host}:{self.port}{self.path}?{self.query_str}"
        )

    @property
    def query_str(self) -> str:
        return "&".join(f"{key}={value}" for key, value in self.query)


class ODDBCredentials(URL):
    model_config = SettingsConfigDict(
        env_prefix="oddb",
    )


class ODDBSettings(CoreSettings):
    model_config = SettingsConfigDict(
        env_prefix="oddb",
    )

    pool_size: PositiveInt
    pool_overflow: PositiveInt
    timeout: PositiveFloat
    retries: PositiveInt


class IMDBCredentials(URL):
    model_config = SettingsConfigDict(
        env_prefix="imdb",
    )


class ExternalAPICredentials(CoreSettings):
    model_config = SettingsConfigDict(
        env_prefix="api",
    )

    fns_key: NonEmptyStr


class MailCredentials(URL):
    model_config = SettingsConfigDict(
        env_prefix="mail",
    )


class VerificationSettings(CoreSettings):
    model_config = SettingsConfigDict(
        env_prefix="verification",
    )

    mail_secret: NonEmptyStr
    password_secret: NonEmptyStr

    sender: EmailStr


class LoggingSettings(CoreSettings):
    model_config = SettingsConfigDict(
        env_prefix="logging",
    )

    level: Level
    is_json: bool


class NetworkSettings(CoreSettings):
    model_config = SettingsConfigDict(
        env_prefix="network",
    )

    trusted_hosts: Sequence[NonEmptyStr]
    allowed_origins: Sequence[HttpUrl] | None = None
    allowed_methods: Sequence[HTTPMethod] | None = None
    allowed_headers: Sequence[NonEmptyStr] | None = None
    are_credentials_allowed: bool
    exposed_headers: Sequence[NonEmptyStr] | None = None
    cache_time: PositiveInt | None = None

    compression_min_size: PositiveInt | None = None
    compression_level: Annotated[PositiveInt | None, Field(le=9)] = None


class DocsSettings(CoreSettings):
    model_config = SettingsConfigDict(
        env_prefix="docs",
    )

    title: Annotated[NonEmptyStr, Field(max_length=50)]
    summary: Annotated[str | None, Field(min_length=5, max_length=150)] = None
    description: Annotated[str | None, Field(min_length=5, max_length=500)] = (
        None
    )
    version: SemanticVersion
    license_name: NonEmptyStr
    license_url: HttpUrl
