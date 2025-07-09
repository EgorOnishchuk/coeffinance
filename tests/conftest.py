from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio

from src.db.db_manager import AsyncpgManager
from src.dependencies import get_db_settings


@pytest.fixture(scope="session")
def db_manager() -> AsyncpgManager:
    return AsyncpgManager(settings=get_db_settings(), clear=True)


@pytest_asyncio.fixture(autouse=True)
async def operate_tables(db_manager: AsyncpgManager) -> AsyncGenerator[None]:
    async with db_manager:
        yield
