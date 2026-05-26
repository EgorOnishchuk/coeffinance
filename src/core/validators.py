from __future__ import annotations

from collections.abc import (
    Callable,
    Mapping,
    MutableSequence,
    Sequence,
)
from enum import StrEnum
from functools import wraps
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Self,
    overload,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    NonNegativeInt,
    PositiveInt,
)
from pydantic.alias_generators import to_camel

from src.core.errors import BusinessError
from src.core.infrastructure.db_models import SQLAlchemyModel

if TYPE_CHECKING:
    from types import CoroutineType

type Serializable = SQLAlchemyModel | CoreValidator

type JSONScalar = str | int | float | bool | None
type JSON = Mapping[str, JSON | JSONScalar] | Sequence[JSON | JSONScalar]
NonEmptyStr = Annotated[str, Field(min_length=1)]


class CoreValidator(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    @classmethod
    @overload
    def from_instance[**P](
        cls, func: Callable[P, CoroutineType[Any, Any, Serializable]]
    ) -> Callable[P, CoroutineType[Any, Any, Self]]:
        pass

    @classmethod
    @overload
    def from_instance[**P](
        cls, func: Callable[P, CoroutineType[Any, Any, Serializable | None]]
    ) -> Callable[P, CoroutineType[Any, Any, Self | None]]:
        pass

    @classmethod
    def from_instance[**P](
        cls, func: Callable[P, CoroutineType[Any, Any, Serializable | None]]
    ) -> Callable[P, CoroutineType[Any, Any, Self | None]]:
        @wraps(func)  # type: ignore[arg-type]
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> Self | None:
            res = await func(*args, **kwargs)
            return cls.model_validate(res) if res is not None else res

        return wrapper  # type: ignore[return-value] # https://github.com/python/mypy/issues/18635.


class OrderBy(StrEnum):
    ASC = "asc"
    DESC = "desc"


class OffsetPage[SchemaT: CoreValidator](CoreValidator):
    items: Sequence[SchemaT]
    total: NonNegativeInt

    page: PositiveInt
    size: PositiveInt
    pages: NonNegativeInt


class CursorPage[SchemaT: CoreValidator](CoreValidator):
    items: Sequence[SchemaT]
    total: NonNegativeInt

    current_page: str | None = None
    previous_page: str | None = None
    next_page: str | None = None


class OffsetPagination(CoreValidator):
    page: PositiveInt = 1
    size: PositiveInt


class OffsetSortedPagination(OffsetPagination):
    order_by: OrderBy


class CursorPagination(CoreValidator):
    next_page: str | None = None
    size: PositiveInt


class CursorSortedPagination(CursorPagination):
    order_by: OrderBy


class PublicError(CoreValidator):
    type: Annotated[NonEmptyStr, Field(examples=["SomeError."])]
    details: Annotated[
        Mapping[NonEmptyStr, JSON],
        Field(
            examples=[
                {
                    "Make sure": "X is correct",
                    "Contact with": ["Y", "Z"],
                }
            ],
        ),
    ] | None = None


def check_not_empty[Item](
    seq: Sequence[Item], exc: type[BusinessError]
) -> Sequence[Item]:
    if not seq:
        raise exc

    return seq
