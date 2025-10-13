import re
from collections.abc import Callable, Sequence
from enum import StrEnum
from functools import wraps
from types import CoroutineType
from typing import Annotated, Any, Final, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    NonNegativeInt,
    PositiveInt,
)
from pydantic.alias_generators import to_camel

type JSON = dict[str, JSON] | list[JSON] | str | int | float | bool | None
type JSONDict = dict[str, JSON]


ENDPOINT: Final = re.compile(
    r"^/(?:[a-z0-9\-._~]+(?:/[a-z0-9\-._~]+)*)?/?$",
    re.IGNORECASE,
)
SHA_1: Final = re.compile(
    r"^[a-f0-9]{40}$",
    re.IGNORECASE,
)

NonEmptyStr = Annotated[str, Field(min_length=1)]


class Schema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        use_enum_values=True,
    )

    @classmethod
    def from_instance_or_none[**P](
        cls, func: Callable[P, CoroutineType[Any, Any, object]]
    ) -> Callable[P, CoroutineType[Any, Any, Self | None]]:
        @wraps(func)  # type: ignore[arg-type] # MyPy limitation when dealing with Callables, having a covariant return type. Not confirmed by Pyright.
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> Self | None:
            result = await func(*args, **kwargs)
            return cls.model_validate(result) if result is not None else result

        return wrapper  # type: ignore[return-value] # MyPy doesn't support CoroutineType properly (unlike Pyright): https://github.com/python/mypy/issues/18635.

    @classmethod
    def from_instance[**P](
        cls, func: Callable[P, CoroutineType[Any, Any, object]]
    ) -> Callable[P, CoroutineType[Any, Any, Self]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> Self:
            result = await func(*args, **kwargs)
            return cls.model_validate(result)

        return wrapper  # type: ignore[return-value] # MyPy doesn't support CoroutineType properly (unlike Pyright): https://github.com/python/mypy/issues/18635.


class DBSchema(Schema):
    id: Annotated[int, Field(frozen=True)]


class OrderBy(StrEnum):
    ASC = "asc"
    DESC = "desc"


class BaseOffsetPage[SchemaT: Schema](Schema):
    items: Sequence[SchemaT]
    total: NonNegativeInt

    page: PositiveInt
    size: PositiveInt
    pages: NonNegativeInt


class BaseCursorPage[SchemaT: Schema](Schema):
    items: Sequence[SchemaT]
    total: NonNegativeInt

    current_page: str | None = None
    previous_page: str | None = None
    next_page: str | None = None


class OffsetSearch(Schema):
    page: PositiveInt = 1
    size: PositiveInt


class OffsetSortingSearch(OffsetSearch):
    order_by: OrderBy


class CursorSearch(Schema):
    next_page: str | None = None
    size: PositiveInt


class CursorSortingSearch(CursorSearch):
    order_by: OrderBy


class PublicError(Schema):
    reason: Annotated[NonEmptyStr, Field(examples=["ABC went wrong."])]
    ways_to_solve: Annotated[
        tuple[NonEmptyStr, ...],
        Field(
            min_length=1,
            max_length=5,
            examples=[
                ("Make sure X is correct.", "Try to do Y.", "Contact with Z.")
            ],
        ),
    ]
