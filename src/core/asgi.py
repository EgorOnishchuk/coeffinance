from __future__ import annotations

from enum import IntEnum, StrEnum
from http import HTTPStatus
from typing import (
    Literal, TYPE_CHECKING,
    Any,
)

import fastapi.openapi.utils as openapi
from cadwyn import Cadwyn, VersionedAPIRouter
from dishka.integrations.fastapi import DishkaRoute, setup_dishka
from fastapi import APIRouter

from src.core.validators import PublicError

if TYPE_CHECKING:
    from collections.abc import Iterable

    from dishka import AsyncContainer


class FastAPIExtended(Cadwyn):
    def __init__(
        self,
        *args: Any,
        routers: Iterable[APIRouter],
        container: AsyncContainer,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            *args,
            api_version_parameter_name="version",
            api_version_format="string",
            api_version_location="path",
            **kwargs,
        )

        self.generate_and_include_versioned_routers(*routers)

        setup_dishka(container, self)

        openapi.validation_error_response_definition = (
            PublicError.model_json_schema()
        )


class RouterExtended(VersionedAPIRouter):
    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs, route_class=DishkaRoute)
