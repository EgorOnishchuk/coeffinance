import pytest_asyncio
from dishka import AsyncContainer

from src.companies.services import CompanyNationalService


@pytest_asyncio.fixture
async def company_service(container: AsyncContainer) -> CompanyNationalService:
    return await container.get(CompanyNationalService)
