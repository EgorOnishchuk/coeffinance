from collections.abc import AsyncGenerator

from dishka import Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.deps.base import BaseProvider
from src.core.settings import DBCredentials, DBPoolSettings
from src.core.utils.db_managers import DBManager, SQLAlchemyCompatible, SQLAlchemyDBManager


class SQLAlchemyProvider(BaseProvider):
    def __init__(self, root_model: type[SQLAlchemyCompatible]) -> None:
        super().__init__()
        self._root_model = root_model

        _credentials, _settings = DBCredentials(), DBPoolSettings()
        self._engine = create_async_engine(_credentials.dsn, **_settings.model_dump(by_alias=True))
        self._Session = async_sessionmaker(self._engine, expire_on_commit=False)

    @provide(provides=DBManager)
    def get_manager(self) -> SQLAlchemyDBManager:
        return SQLAlchemyDBManager(root_model=self._root_model, engine=self._engine)

    @provide(scope=Scope.REQUEST)
    async def get_session(self) -> AsyncGenerator[AsyncSession]:
        async with self._Session() as session:
            try:
                yield session
                await session.commit()
            except:
                await session.rollback()
                raise
            finally:
                await session.close()
