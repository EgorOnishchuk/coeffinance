from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase


class SQLAlchemyModel(AsyncAttrs, DeclarativeBase):
    __abstract__ = True
