from decimal import Decimal
from enum import StrEnum
from typing import Annotated

from pydantic import Field

from src.core.schemas import NonEmptyStr, Schema


class Deviation(StrEnum):
    LOWER = "Lower"
    UPPER = "Upper"


class Ratio(Schema):
    name: Annotated[NonEmptyStr, Field(max_length=20)]
    value: Decimal
    deviation: Deviation | None = None


class Analytics(Schema):
    name: Annotated[NonEmptyStr, Field(max_length=30)]
    ratios: list[Ratio]
