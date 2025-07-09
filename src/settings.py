import logging
import re
from typing import Annotated, ClassVar

from pydantic import (
    AfterValidator,
    EmailStr,
    Field,
    HttpUrl,
    PositiveFloat,
    PositiveInt,
    field_validator,
)
from pydantic_extra_types.semantic_version import SemanticVersion
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.schemas import NonEmptyStr

LOGGER: logging.Logger = logging.getLogger("uvicorn.error")

ENDPOINT: re.Pattern[str] = re.compile(
    r"^/(?:[A-Za-z0-9\-._~]+(?:/[A-Za-z0-9\-._~]+)*)?/?$",
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class APISettings(Settings):
    host: Annotated[NonEmptyStr, Field(validation_alias="api_host")]
    port: Annotated[PositiveInt, Field(le=65535, validation_alias="api_port")]

    timeout: Annotated[
        PositiveFloat,
        Field(validation_alias="external_api_timeout"),
    ] = 10.0


class DBSettings(Settings):
    host: Annotated[NonEmptyStr, Field(validation_alias="db_host")]
    user: Annotated[NonEmptyStr, Field(validation_alias="db_user")]
    password: Annotated[NonEmptyStr, Field(validation_alias="db_password")]
    db_name: NonEmptyStr

    pool_min_size: Annotated[PositiveInt, Field(serialization_alias="min_size")] = 10
    pool_max_size: Annotated[PositiveInt, Field(serialization_alias="max_size")] = 10
    max_queries: PositiveInt = 50000
    max_inactive_connection_lifetime: PositiveFloat = 300.0
    timeout: Annotated[PositiveFloat, Field(validation_alias="db_timeout")] = 5.0


class TrustedHostsSettings(Settings):
    hosts: Annotated[list[NonEmptyStr] | None, Field(alias="allowed_hosts")] = [
        "localhost",
        "test",
    ]


class CORSSettings(Settings):
    methods: ClassVar[set[str]] = {
        "GET",
        "HEAD",
        "POST",
        "PUT",
        "DELETE",
        "CONNECT",
        "OPTIONS",
        "TRACE",
        "PATCH",
    }

    allowed_origins: Annotated[
        list[HttpUrl] | None,
        Field(serialization_alias="allow_origins"),
    ] = None
    allowed_origin_regex: Annotated[
        str | None,
        Field(serialization_alias="allow_origin_regex"),
    ] = None
    allowed_methods: Annotated[
        list[NonEmptyStr] | None,
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

    @field_validator("allowed_methods")
    @classmethod
    def check_existence(cls, value: list[str] | None) -> list[str] | None:
        if value is not None and set(value) - cls.methods:
            raise ValueError("Some methods are not defined in HTTP specification.")

        return value


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
