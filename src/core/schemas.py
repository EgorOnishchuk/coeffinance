import re
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

type JSON = dict[str, JSON] | list[JSON] | str | int | float | bool | None
type JSONDict = dict[str, JSON]


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


class DBSchema(Schema):
    """
    ID is a «hidden» primary key here — see models.py for details.
    """

    id: Annotated[int, Field(exclude=True)]


class DBNamingConvention(Schema):
    ix: str = "ix_%(column_0_label)s"
    uq: str = "uq_%(table_name)s_%(column_0_name)s"
    ck: str = "ck_%(table_name)s_%(constraint_name)s"
    fk: str = "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"
    pk: str = "pk_%(table_name)s"


class Error(Schema):
    """
    Intended to provide an additional context to responses that do not allow for a clear determination of an error at
    the protocol level — see errors.py for details.
    """

    reason: Annotated[NonEmptyStr, Field(examples=["ABC went wrong."])]
    ways_to_solve: Annotated[
        tuple[NonEmptyStr, ...],
        Field(
            min_length=1,
            max_length=5,
            examples=[("Make sure X is correct.", "Try to do Y.", "Contact with Z.")],
        ),
    ]
