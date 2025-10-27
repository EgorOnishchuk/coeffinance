from decimal import Decimal
from enum import StrEnum
from functools import total_ordering
from typing import Annotated, Self

from pydantic import Field

from src.core.schemas import NonEmptyStr, Schema


class Deviation(StrEnum):
    LOWER = "Lower"
    UPPER = "Upper"


@total_ordering
class Ratio(Schema):
    name: Annotated[NonEmptyStr, Field(max_length=20)]
    value: Decimal
    deviation: Deviation | None = None

    def __gt__(self, other: Self) -> bool:
        return self.name > other.name


@total_ordering
class Analytics(Schema):
    name: Annotated[NonEmptyStr, Field(max_length=30)]
    ratios: list[Ratio]

    def __gt__(self, other: Self) -> bool:
        return self.name > other.name
