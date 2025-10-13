from dataclasses import dataclass
from typing import override

from polyfactory import AsyncPersistenceProtocol, BaseFactory
from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from src.core.db.models import SQLAlchemyModel, SQLAlchemyPKModel
from src.core.db.sessions import SQLAlchemySession
from src.core.schemas import (
    CursorSortingSearch,
    OffsetSortingSearch,
    Schema,
)


class ExtendedPydanticFactory[Model: Schema](ModelFactory[Model]):
    __is_base_factory__ = True
    __check_model__ = True
    __set_as_default_factory_for_type__ = True

    __randomize_collection_length__ = True
    __min_collection_length__ = 1
    __max_collection_length__ = 10


class OffsetSortingSearchFactory(ExtendedPydanticFactory[OffsetSortingSearch]):
    pass


class CursorSortingSearchFactory(ExtendedPydanticFactory[CursorSortingSearch]):
    pass


@dataclass(kw_only=True, slots=True, frozen=True)
class SQLAlchemyPersistence[Model: SQLAlchemyPKModel](
    AsyncPersistenceProtocol[Model]
):
    _session: SQLAlchemySession

    @override
    async def save(self, data: Model) -> Model:
        self._session.add(data)
        await self._session.flush()

        await self._session.refresh(data)
        await self._session.load_all(data)
        return data

    @override
    async def save_many(self, data: list[Model]) -> list[Model]:
        self._session.add_all(data)
        await self._session.flush()

        for item in data:
            await self._session.refresh(item)
            await self._session.load_all(item)

        return data


class ExtendedSQLAlchemyFactory[Model: SQLAlchemyModel](
    SQLAlchemyFactory[Model]
):
    __is_base_factory__ = True
    __check_model__ = True

    # To avoid recursion: __set_relationship__ does not look up the
    # corresponding factories (__set_as_default_factory_for_type__ does not make
    # sense in the case of SQLAlchemy), but immediately uses the models «as is».
    # This field should be selectively set to True directly in the tests,
    # depending on the target model.
    __set_relationships__ = False
    __set_association_proxy__ = False

    @classmethod
    def _batch[Relation: SQLAlchemyModel](
        cls, factory: type[BaseFactory[Relation]], *, min_: int, max_: int
    ) -> list[Relation]:
        return factory.batch(cls.__random__.randint(min_, max_))
