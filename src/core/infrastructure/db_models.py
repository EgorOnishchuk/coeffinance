from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from itertools import zip_longest
from typing import Any, override

from sqlalchemy import (
    CheckConstraint,
    Column,
    Compiled,
    DateTime,
    Dialect,
    FunctionElement,
    MetaData,
    UnaryExpression,
    func,
    inspect,
)
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import (
    DeclarativeBase,
    InstrumentedAttribute,
    Mapped,
    MappedColumn,
    mapped_column,
)
from sqlalchemy.types import TypeDecorator

from src.core.errors import SysError
from src.core.validators import OrderBy


@dataclass(kw_only=True, slots=True, frozen=True)
class SQLNamingConvention:
    ix: str = "ix_%(column_0_label)s"
    uq: str = "uq_%(table_name)s_%(column_0_name)s"
    ck: str = "ck_%(table_name)s_%(constraint_name)s"
    fk: str = "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"
    pk: str = "pk_%(table_name)s"


class SQLAlchemyModel(AsyncAttrs, DeclarativeBase):
    __abstract__ = True
    metadata = MetaData(naming_convention=asdict(SQLNamingConvention()))
    docs: Mapping[str, str] = {}


class SQLAlchemyPKModel(SQLAlchemyModel):
    __abstract__ = True

    @property
    def pk_columns(self) -> tuple[Column[Any], ...]:
        return inspect(self).mapper.primary_key

    @property
    def pk_values(self) -> tuple[Any, ...]:
        if (identity := inspect(self).identity) is not None:
            return identity

        raise SysError(
            f"{type(self)} has no primary keys but marked as "
            f"implementing PK interface."
        )


class SQLAlchemyIDModel(SQLAlchemyPKModel):
    __abstract__ = True
    docs: Mapping[str, str] = {
        "id": "Is a «hidden» primary key here. Each table used in the "
        "public API should have an additional «exposed» unique key, "
        "which should preferably be natural (not surrogate) for "
        "usability."
    }

    id: Mapped[int] = mapped_column(
        primary_key=True,
        doc=docs["id"],
        comment=docs["id"],
    )


class utcnow(FunctionElement[datetime]):  # noqa: N801
    type = DateTime()
    inherit_cache = True


@compiles(utcnow, "postgresql")
def pg_utcnow(element: utcnow, compiler: Compiled, **kwargs: Any) -> str:
    return "TIMEZONE('utc', CURRENT_TIMESTAMP)"


class UTCDateTime(TypeDecorator[datetime]):
    impl = DateTime(timezone=True)
    cache_ok = True

    @override
    def process_result_value(
        self, value: datetime | None, dialect: Dialect
    ) -> datetime | None:
        if value is None:
            return None
        return value.astimezone(UTC)


def get_sortables(
    columns: Iterable[InstrumentedAttribute[Any]],
    orders: Iterable[OrderBy],
) -> tuple[UnaryExpression[Any], ...]:
    return tuple(
        getattr(column, order)()
        for column, order in zip_longest(columns, orders, fillvalue=OrderBy.ASC)
    )


def get_length_constraint(
    field: MappedColumn[Any],
    *,
    min_: int,
) -> CheckConstraint:
    return CheckConstraint(
        func.char_length(field) >= min_,
        name=f"{field.column.key}_min_len",
    )
