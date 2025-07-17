import re
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

ENDPOINT = re.compile(
    r"^/(?:[a-z0-9\-._~]+(?:/[a-z0-9\-._~]+)*)?/?$",
    re.IGNORECASE,
)
SHA_1 = re.compile(
    r"^[a-f0-9]{40}$",
    re.IGNORECASE,
)

NonEmptyStr = Annotated[str, Field(min_length=1)]


class Schema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class Error(Schema):
    reason: Annotated[NonEmptyStr, Field(examples=["Not available"])]
    ways_to_solve: Annotated[
        list[NonEmptyStr],
        Field(
            min_length=1,
            examples=[["Try again", "Try later", "Contact to support"]],
        ),
    ]
