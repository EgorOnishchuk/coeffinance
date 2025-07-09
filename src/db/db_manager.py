from abc import ABC, abstractmethod
from asyncio import CancelledError
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from types import TracebackType
from typing import Any

from asyncpg import Pool, create_pool

from src.data_access_layer import AsyncpgDAL
from src.errors import DBConnError
from src.settings import DBSettings


@dataclass(kw_only=True)
class DBManager(ABC):
    settings: DBSettings
    clear: bool = False

    def __post_init__(self) -> None:
        self.timeout = self.settings.timeout

    @abstractmethod
    @asynccontextmanager
    async def get_conn(self) -> AsyncGenerator[Any]:
        pass

    @abstractmethod
    async def __aenter__(self) -> None:
        pass

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        pass


class AsyncpgManager(DBManager):
    pool: Pool | None = None

    @asynccontextmanager
    async def get_conn(self) -> AsyncGenerator[Any]:
        assert self.pool is not None

        try:
            async with self.pool.acquire(timeout=self.timeout) as conn, conn.transaction():
                yield conn
        except CancelledError as exc:
            raise DBConnError from exc

    async def __aenter__(self) -> None:
        self.pool = await create_pool(
            f"postgresql://{self.settings.user}:{self.settings.password}@{self.settings.host}/{self.settings.db_name}",
            **self.settings.model_dump(
                by_alias=True,
                exclude={"dsn", "timeout", "user", "password", "host", "db_name"},
            ),
        )

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        assert self.pool is not None

        if self.clear:
            async with self.get_conn() as conn:
                await conn.execute(
                    f"TRUNCATE {', '.join(cls.schema.__name__.lower() for cls in AsyncpgDAL.__subclasses__())}",
                )
        await self.pool.close()
