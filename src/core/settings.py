from http import HTTPMethod
from typing import Annotated

from pydantic import (
    AfterValidator,
    EmailStr,
    Field,
    HttpUrl,
    PositiveFloat,
    PositiveInt,
)
from pydantic_extra_types.semantic_version import SemanticVersion
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.schemas import ENDPOINT, SHA_1, NonEmptyStr


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class DBCredentials(Settings):
    schema_: Annotated[NonEmptyStr, Field(validation_alias="db_schema")]
    host: Annotated[NonEmptyStr, Field(validation_alias="db_host")]
    user: Annotated[NonEmptyStr, Field(validation_alias="db_user")]
    password: Annotated[NonEmptyStr, Field(validation_alias="db_password")]
    db_name: NonEmptyStr

    @property
    def dsn(self) -> str:
        return f"{self.schema_}://{self.user}:{self.password}@{self.host}/{self.db_name}"


class DBPoolSettings(Settings):
    size: Annotated[PositiveInt, Field(validation_alias="db_pool_size", serialization_alias="pool_size")] = 10
    overflow: Annotated[PositiveInt, Field(validation_alias="db_pool_overflow", serialization_alias="max_overflow")] = 3
    timeout: Annotated[PositiveFloat, Field(validation_alias="db_timeout", serialization_alias="pool_timeout")] = 5.0


class ExternalAPISettings(Settings):
    api_fns_token: Annotated[str, Field(pattern=SHA_1)]

    timeout: Annotated[
        PositiveFloat,
        Field(validation_alias="external_api_timeout"),
    ] = 10.0


class TrustedHostsSettings(Settings):
    hosts: Annotated[list[NonEmptyStr] | None, Field(alias="allowed_hosts")] = [
        "localhost",
        "test",
    ]


class CORSSettings(Settings):
    allowed_origins: Annotated[
        list[HttpUrl] | None,
        Field(serialization_alias="allow_origins"),
    ] = None
    allowed_origin_regex: Annotated[
        str | None,
        Field(serialization_alias="allow_origin_regex"),
    ] = None
    allowed_methods: Annotated[
        list[HTTPMethod] | None,
        Field(serialization_alias="allow_methods"),
    ] = None
    allowed_headers: Annotated[
        list[NonEmptyStr] | None,
        Field(serialization_alias="allow_headers"),
    ] = None
    is_credentials: Annotated[
        bool | None,
        Field(serialization_alias="allow_credentials"),
    ] = None
    exposed_headers: Annotated[
        list[NonEmptyStr] | None,
        Field(serialization_alias="expose_headers"),
    ] = None
    cache_time: Annotated[PositiveInt | None, Field(serialization_alias="max_age")] = None


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
    description: Annotated[str | None, Field(min_length=5, max_length=500)] = None
    version: Annotated[SemanticVersion, AfterValidator(lambda value: str(value))]
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
