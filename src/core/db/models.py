from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from types import MappingProxyType
from typing import Any, cast, override

from sqlalchemy import (
    CheckConstraint,
    Column,
    Compiled,
    DateTime,
    Dialect,
    FunctionElement,
    MetaData,
    func,
    inspect,
)
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator


@dataclass(kw_only=True, slots=True, frozen=True)
class DBNamingConvention:
    ix: str = "ix_%(column_0_label)s"
    uq: str = "uq_%(table_name)s_%(column_0_name)s"
    ck: str = "ck_%(table_name)s_%(constraint_name)s"
    fk: str = "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"
    pk: str = "pk_%(table_name)s"


class SQLAlchemyModel(AsyncAttrs, DeclarativeBase):
    __abstract__ = True
    metadata = MetaData(naming_convention=asdict(DBNamingConvention()))
    docs: MappingProxyType[str, str] = MappingProxyType({})


class SQLAlchemyPKModel(SQLAlchemyModel):
    __abstract__ = True

    @property
    def pk_columns(self) -> tuple[Column[Any], ...]:
        return inspect(self).mapper.primary_key

    @property
    def pk_values(self) -> tuple[Any, ...]:
        return cast(tuple[Any, ...], inspect(self).identity)


class SQLAlchemyIDModel(SQLAlchemyPKModel):
    __abstract__ = True
    docs: MappingProxyType[str, str] = MappingProxyType(
        {
            "id": "Is a «hidden» primary key here. Each table used in the "
            "public API should have an additional «exposed» unique key, "
            "which should preferably be natural (not surrogate) for "
            "usability."
        }
    )

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


def get_length_constraint(
    field: Mapped[str], *, min_: int, name: str
) -> CheckConstraint:
    return CheckConstraint(
        func.char_length(field) >= min_,
        name=name,
    )
