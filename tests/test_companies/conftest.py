import pytest_asyncio
from dishka import AsyncContainer

from src.companies.service import CompanyService


@pytest_asyncio.fixture
async def company_service(container: AsyncContainer) -> CompanyService:
    return await container.get(CompanyService)
