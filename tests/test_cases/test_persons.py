import pytest
from httpx import AsyncClient

from tests.test_cases.base import TestAPI


class TestPersonAPI(TestAPI):
    route: str = "/api/persons"

    @pytest.mark.asyncio
    async def test_create(self, session: AsyncClient) -> None:
        person = (await session.post(self.route)).json()

        assert all(
            (
                person["firstName"] == "Rosa",
                person["lastName"] == "Sanford",
                person["birthdate"] == "1999-03-16",
                person["gender"] == "female",
            ),
        )
