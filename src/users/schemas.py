from functools import total_ordering
from typing import Annotated, Self

from fastapi_users.schemas import (
    BaseUserCreate,
    BaseUserUpdate,
    CreateUpdateDictModel,
)
from pydantic import EmailStr, Field

from src.core.validators import CoreValidator

Nickname = Annotated[
    str, Field(min_length=6, max_length=30, examples=["Ivan Ivanov"])
]
Email = Annotated[EmailStr, Field(max_length=256, examples=["ivanov@mail.ru"])]


class UserCreate(CoreValidator, BaseUserCreate):
    nickname: Nickname
    email: Email
    password: Annotated[str, Field(examples=["-¯#P'Hä¯Nðfº2>+¶;Öðº±í,M»)î¾æd"])]


@total_ordering
class User(CoreValidator, CreateUpdateDictModel):
    nickname: Nickname
    email: Email
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False

    def __gt__(self, other: Self) -> bool:
        return self.nickname > other.nickname

    def __eq__(self, other: Self) -> bool:
        return self.nickname == other.nickname


class UserUpdate(CoreValidator, BaseUserUpdate):
    nickname: Annotated[
        str | None, Field(min_length=6, max_length=30, examples=["Ivan Ivanov"])
    ] = None
    email: Annotated[
        EmailStr | None, Field(max_length=256, examples=["ivanov@mail.ru"])
    ] = None
