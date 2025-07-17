from typing import cast

from dishka import make_async_container

from src.core.deps.base import SettingsProvider, UvicornLoggerProvider
from src.core.deps.db_managers import SQLAlchemyProvider
from src.core.deps.http_clients import HTTPXProvider
from src.core.models import SQLAlchemyModel
from src.core.utils.db_managers import SQLAlchemyCompatible

container = make_async_container(
    SettingsProvider(),
    UvicornLoggerProvider(),
    HTTPXProvider(),
    SQLAlchemyProvider(cast(type[SQLAlchemyCompatible], SQLAlchemyModel)),
)
