from typing import Annotated

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlmodel import Field, SQLModel

from src.core.schemas import DBNamingConvention


class SQLAlchemyModel(AsyncAttrs, DeclarativeBase):
    __abstract__ = True
    metadata = MetaData(naming_convention=DBNamingConvention().model_dump())


class SQLAlchemyIDModel(SQLAlchemyModel):
    """
    Autoincrement is a «hidden» primary key here. Each table used in the public API should have an additional «exposed»
    unique key, which should preferably be natural (not surrogate) for usability.
    """

    __abstract__ = True
    id: Mapped[int] = mapped_column(primary_key=True)


class SQLModelBase(SQLModel, AsyncAttrs):
    metadata = MetaData(naming_convention=DBNamingConvention().model_dump())


class SQLModelID(SQLModelBase):
    """
    Autoincrement is a «hidden» primary key here. Each table used in the public API should have an additional «exposed»
    unique key, which should preferably be natural (not surrogate) for usability.
    """

    id: Annotated[int, Field(primary_key=True)]
