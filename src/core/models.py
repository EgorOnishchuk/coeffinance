from typing import Annotated

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlmodel import Field, SQLModel

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class SQLAlchemyModel(AsyncAttrs, DeclarativeBase):
    """
    Autoincrement is a «hidden» primary key here. Each table used in an external API should have an additional «exposed»
    key, which should preferably be natural (not surrogate) for usability.
    """

    __abstract__ = True
    metadata = MetaData(naming_convention=convention)

    id: Mapped[int] = mapped_column(primary_key=True)


class SQLModelBase(SQLModel, AsyncAttrs):
    """
    Autoincrement is a «hidden» primary key here. Each table used in an external API should have an additional «exposed»
    key, which should preferably be natural (not surrogate) for usability.
    """

    metadata = MetaData(naming_convention=convention)

    id: Annotated[int, Field(primary_key=True)]
