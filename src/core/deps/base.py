import logging

from dishka import Provider, Scope, provide

from src.core.settings import (
    AuthSettings,
    CacheCredentials,
    DBCredentials,
    DBPoolSettings,
    EmailSettings,
    ExternalAPISettings,
)
from src.core.utils.loggers import UVICORN_LOGGER, Logger


class BaseProvider(Provider):
    scope = Scope.APP


class SettingsProvider(BaseProvider):
    @provide
    def get_db_credentials(self) -> DBCredentials:
        return DBCredentials()

    @provide
    def get_db_pool_settings(self) -> DBPoolSettings:
        return DBPoolSettings()

    @provide
    def get_cache_credentials(self) -> CacheCredentials:
        return CacheCredentials()

    @provide
    def get_auth_settings(self) -> AuthSettings:
        return AuthSettings()

    @provide
    def get_email_settings(self) -> EmailSettings:
        return EmailSettings()

    @provide
    def get_external_api_settings(self) -> ExternalAPISettings:
        return ExternalAPISettings()


class UvicornLoggerProvider(BaseProvider):
    @provide(provides=Logger)
    def get_logger(self) -> logging.Logger:
        return logging.getLogger(UVICORN_LOGGER)
