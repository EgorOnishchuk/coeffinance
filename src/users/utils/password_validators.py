from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Annotated, ClassVar, Literal, override

from pydantic import AliasPath, Field, NonNegativeInt
from zxcvbn import zxcvbn

from src.core.schemas import NonEmptyStr, Schema


class Report(Schema):
    is_strong: bool
    score: NonNegativeInt
    strength: Literal["Very Weak", "Weak", "Medium", "Strong", "Very Strong"]
    improvements: Iterable[NonEmptyStr]


class ZXCVBNReport(Report):
    improvements: Annotated[
        Iterable[NonEmptyStr],
        Field(validation_alias=AliasPath("feedback", "suggestions")),
    ]


class PasswordValidator(ABC):
    @abstractmethod
    def validate(self, password: str, *, related: Iterable[str] = ()) -> Report:
        raise NotImplementedError


class ZXCVBNValidator(PasswordValidator):
    STRENGTH: ClassVar = (
        "Very Weak",
        "Weak",
        "Medium",
        "Strong",
        "Very Strong",
    )
    REQUIRED_SCORE: ClassVar = 3

    @override
    def validate(
        self,
        password: str,
        *,
        related: Iterable[str] = (),
    ) -> Report:
        report = zxcvbn(password, user_inputs=related)

        return ZXCVBNReport.model_validate(
            {
                "is_strong": report["score"] >= self.REQUIRED_SCORE,
                "strength": self.STRENGTH[report["score"]],
                **report,
            }
        )
