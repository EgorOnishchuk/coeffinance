from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, FastAPI

from src.core.errors import OpenAPIError
from src.core.schemas import JSON, JSONDict


class DishkaRouter(APIRouter):
    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs, route_class=DishkaRoute)


@dataclass(kw_only=True, slots=True, frozen=True)
class RouterManager(ABC):
    app: FastAPI

    @abstractmethod
    async def attach(self) -> None:
        raise NotImplementedError


@dataclass(kw_only=True)
class OpenAPIEditor:
    """
    Intended for one-time and targeted editing of the docs where high-level tools cannot be used. For example,
    libraries that provide ready-made boilerplate routers may hardcode their routes' metadata.
    """

    openapi: JSONDict

    def __post_init__(self) -> None:
        try:
            self.schemas: JSONDict = self.openapi["components"]["schemas"]  # type: ignore[index, call-overload, assignment]
            self.paths: JSONDict = self.openapi["paths"]  # type: ignore[call-overload, assignment]
        except (KeyError, IndexError) as exc:
            raise OpenAPIError(exc.args[0]) from exc

    def override_schemas(self, models: Iterable[str], source: JSONDict) -> None:
        for model in models:
            try:
                self.schemas[model] = source  # type: ignore[call-overload]
            except (KeyError, IndexError) as exc:
                raise OpenAPIError(exc.args[0]) from exc

    def remove_elements(self, target: str, paths: JSON | None = None) -> None:
        if paths is None:
            paths = self.paths

        if isinstance(paths, dict):
            paths.pop(target, None)
            for value in paths.values():
                self.remove_elements(target, value)
        elif isinstance(paths, list):
            for item in paths:
                self.remove_elements(target, item)
