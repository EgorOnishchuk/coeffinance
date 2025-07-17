import logging

from dishka import Provider, Scope, provide

from src.core.settings import ExternalAPISettings
from src.core.utils.loggers import UVICORN_LOGGER, Logger


class BaseProvider(Provider):
    scope = Scope.APP


class SettingsProvider(BaseProvider):
    @provide
    def get_external_api_settings(self) -> ExternalAPISettings:
        return ExternalAPISettings()


class UvicornLoggerProvider(BaseProvider):
    @provide(provides=Logger)
    def get_logger(self) -> logging.Logger:
        return logging.getLogger(UVICORN_LOGGER)
