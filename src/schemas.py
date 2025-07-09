from collections.abc import Awaitable, Callable, Sequence
from functools import wraps
from typing import Annotated, Any, Generic, TypeVar, cast

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

NonEmptyStr = Annotated[str, Field(min_length=1)]

SchemaT = TypeVar("SchemaT", bound="Schema")


class Schema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    @staticmethod
    def to_tuple(
        func: Callable[[Any, tuple[Any, ...], Any], Awaitable[Any]],
    ) -> Callable[[Any, SchemaT, Any], Awaitable[Any]]:
        @wraps(func)
        async def wrapper(self: Any, schema: SchemaT, *args: Any, **kwargs: Any) -> Any:
            tuple_ = tuple(schema.model_dump().values())
            return await func(self, tuple_, *args, **kwargs)

        return cast(Callable[[Any, SchemaT, Any], Awaitable[Any]], wrapper)


class OneTransformer(Generic[SchemaT]):
    def __call__(self, res: Any, schema: type[SchemaT]) -> SchemaT:
        return schema(**dict(res))


class ManyTransformer(Generic[SchemaT]):
    def __call__(self, seq: Sequence[Any], schema: type[SchemaT]) -> list[SchemaT]:
        return [schema(**dict(res)) for res in seq]


def from_res(
    transformer: Callable[[Any, type[SchemaT]], Any],
) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            res = await func(self, *args, **kwargs)
            return transformer(res, self.schema)

        return wrapper

    return decorator


def from_dict() -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    return from_res(OneTransformer())


def from_dicts() -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    return from_res(ManyTransformer())


class Error(Schema):
    reason: Annotated[NonEmptyStr, Field(examples=["Not available"])]
    ways_to_solve: Annotated[
        list[NonEmptyStr],
        Field(
            min_length=1,
            examples=[["Try again", "Try later", "Contact to support"]],
        ),
    ]
