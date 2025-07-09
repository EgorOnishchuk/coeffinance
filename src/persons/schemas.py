from typing import Annotated, Literal
from uuid import UUID

from pydantic import AliasChoices, AliasPath, Field, PastDate

from src.schemas import NonEmptyStr, Schema


class PersonCreate(Schema):
    first_name: Annotated[
        NonEmptyStr,
        Field(
            validation_alias=AliasChoices(
                AliasPath("data", 0, "firstname"),
                "firstName",
            ),
            max_length=100,
            examples=["Rosa"],
        ),
    ]
    last_name: Annotated[
        NonEmptyStr,
        Field(
            validation_alias=AliasChoices(AliasPath("data", 0, "lastname"), "lastName"),
            max_length=100,
            examples=["Sanford"],
        ),
    ]

    gender: Annotated[
        Literal["male", "female", "other"],
        Field(validation_alias=AliasPath("data", 0, "gender"), examples=["female"]),
    ]
    birthdate: Annotated[
        PastDate,
        Field(
            validation_alias=AliasPath("data", 0, "birthday"),
            examples=["1999-03-16"],
        ),
    ]


class Person(PersonCreate):
    id: Annotated[UUID, Field(examples=["94e2f14c-4d8f-4d5e-9b4d-e0e2f57597f8"])]
