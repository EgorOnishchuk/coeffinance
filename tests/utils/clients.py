from typing import Any

from src.persons.schemas import PersonCreate
from src.schemas import from_dict


class MockClient:
    schema = PersonCreate

    @from_dict()
    async def request(self, method: str, **kwargs: Any) -> dict[str, Any]:
        return {
            "data": [
                {
                    "id": 1,
                    "firstname": "Rosa",
                    "lastname": "Sanford",
                    "email": "abe.haley@yahoo.com",
                    "phone": "+15516172864",
                    "birthday": "1999-03-16",
                    "gender": "female",
                },
            ],
        }
