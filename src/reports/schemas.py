from datetime import datetime
from typing import Annotated, Generic, TypeVar

from pydantic import Field

from src.persons.schemas import Person, PersonCreate
from src.schemas import Schema

PersonT = TypeVar("PersonT")


class Report(Schema, Generic[PersonT]):
    created_at: Annotated[
        datetime,
        Field(default_factory=datetime.now, examples=["2025-01-01T00:00:00.000000"]),
    ]
    persons: list[PersonT]


class OfficialReport(Report[Person]):
    pass


class CustomReport(Report[PersonCreate]):
    pass
