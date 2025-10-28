from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    TypeVar,
    cast,
    override,
)

import fastapi.openapi.utils as openapi
from cadwyn import Cadwyn, VersionedAPIRouter
from cadwyn.schema_generation import (
    _T_PYDANTIC_MODEL,
    SchemaGenerator,
    _PerFieldValidatorWrapper,
    _PydanticModelWrapper,
    _ValidatorWrapper,
)
from dishka.integrations.fastapi import DishkaRoute, setup_dishka
from starlette.datastructures import State
from starlette.requests import Request

from src.core.schemas import PublicError

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterable

    from dishka import AsyncContainer
    from starlette.responses import Response

    from src.core.middlewares import Middleware


def patch_cadwyn() -> None:
    """
    Temporary fix for generics: https://github.com/zmievsa/cadwyn/pull/303.
    """

    def generate_model_copy(
        self, generator: SchemaGenerator
    ) -> type[_T_PYDANTIC_MODEL]:
        per_field_validators = {
            name: validator.decorator(*validator.fields, **validator.kwargs)(
                validator.func
            )
            for name, validator in self.validators.items()
            if not validator.is_deleted
            and type(validator) == _PerFieldValidatorWrapper  # noqa: E721
        }
        root_validators = {
            name: validator.decorator(**validator.kwargs)(validator.func)
            for name, validator in self.validators.items()
            if not validator.is_deleted and type(validator) == _ValidatorWrapper
        }
        fields = {
            name: field.generate_field_copy(generator)
            for name, field in self.fields.items()
        }

        model_copy = type(self.cls)(
            self.name,
            tuple(
                generator[cast("type[BaseModel]", base)]
                for base in self.cls.__bases__
                if base is not Generic
            ),
            self.other_attributes
            | per_field_validators
            | root_validators
            | fields
            | {
                "__annotations__": generator.annotation_transformer.change_version_of_annotation(
                    self.annotations,
                ),
                "__doc__": self.doc,
                "__qualname__": self.cls.__qualname__.removesuffix(
                    self.cls.__name__
                )
                + self.name,
            },
            __pydantic_generic_metadata__=self.cls.__pydantic_generic_metadata__,
        )

        model_copy.__cadwyn_original_model__ = self.cls
        return model_copy

    _PydanticModelWrapper.generate_model_copy = generate_model_copy


class TypedState(State):
    """
    The default state of an app/request allows to store anything, so
    state-based integrations must be explicitly specified for type checking.
    """

    dishka_container: AsyncContainer  # pyright: ignore[reportUninitializedInstanceVariable]


class ExtendedFastAPI(Cadwyn):
    def __init__(
        self,
        *args: Any,
        routers: Iterable[ExtendedRouter],
        middleware_map: Iterable[Middleware] = (()),
        handling_map: Iterable[HandlingPair[Exception]] = (()),
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

        patch_cadwyn()
        self.generate_and_include_versioned_routers(*routers)

        for middleware, settings in middleware_map:
            self.add_middleware(middleware, *(), **settings)  # pyright: ignore[reportCallIssue] # Specifics of the framework design, not confirmed by MyPy.

        for pair in handling_map:
            self.add_exception_handler(pair.exc, pair.handler)  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType] # Does not affect anything in runtime, as Extended Request is only for type checking.

        setup_dishka(container, self)
        self.state = cast(TypedState, self.state)

        openapi.validation_error_response_definition = (
            PublicError.model_json_schema()
        )


class ExtendedRequest(Request):
    @property
    @override
    def state(self) -> TypedState:
        return cast(TypedState, super().state)


class ExtendedRouter(VersionedAPIRouter):
    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs, route_class=DishkaRoute)


class Architecture(StrEnum):
    # This implies a combination of the REST resource model and RPC verb
    # endpoints (where actions go beyond the CRUD model).
    JSON_API = "json-api"


ExcT_co = TypeVar("ExcT_co", bound=Exception, covariant=True)


@dataclass(kw_only=True, slots=True, frozen=True)
class HandlingPair(Generic[ExcT_co]):
    exc: type[ExcT_co] | int
    handler: Callable[[ExtendedRequest, ExcT_co], Awaitable[Response]]
