from datetime import date
from decimal import Decimal
from functools import partial, total_ordering
from typing import Annotated, ClassVar, Self

from pydantic import (
    AfterValidator,
    ConfigDict,
    Field,
    PositiveInt,
    field_validator,
    model_validator,
)

from src.core.validators import CoreValidator, NonEmptyStr, check_not_empty
from src.reports.errors import (
    EmptyRatiosError,
    NormalRangeError,
    TotalWeightError,
)


@total_ordering
class Ratio(CoreValidator):
    model_config = ConfigDict(
        frozen=True,
    )

    name: Annotated[NonEmptyStr, Field(max_length=20)]
    value: Decimal
    weight: PositiveInt

    min_normal_value: Decimal
    max_normal_value: Decimal

    @model_validator(mode="after")
    def check_normal_range(self) -> Self:
        if self.min_normal_value > self.max_normal_value:
            raise NormalRangeError

        return self

    @property
    def is_normal(self) -> bool:
        return self.min_normal_value <= self.value <= self.max_normal_value

    def __gt__(self, other: Self) -> bool:
        return self.name > other.name

    def __eq__(self, other: Self) -> bool:
        return self.name == other.name


@total_ordering
class Report(CoreValidator):
    model_config = ConfigDict(
        frozen=True,
    )

    total_weight: ClassVar[PositiveInt] = 100

    name: Annotated[NonEmptyStr, Field(max_length=30)]
    period_start: date
    period_end: date

    ratios: Annotated[
        set[Ratio],
        AfterValidator(partial(check_not_empty, exc=EmptyRatiosError)),
    ]

    @field_validator("ratios")
    @classmethod
    def check_weights(cls, ratios: set[Ratio]) -> set[Ratio]:
        if sum(ratio.weight for ratio in ratios) != cls.total_weight:
            raise TotalWeightError

        return ratios

    @property
    def score(self) -> int:
        return sum(
            ratio.weight if ratio.is_normal else 0 for ratio in self.ratios
        )

    def __gt__(self, other: Self) -> bool:
        return self.name > other.name

    def __eq__(self, other: Self) -> bool:
        return self.name == other.name
