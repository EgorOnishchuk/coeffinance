from typing import Annotated

from fastapi_users.schemas import BaseUser, BaseUserCreate, BaseUserUpdate
from pydantic import EmailStr, Field

from src.core.schemas import DBSchema, Schema


class ExtendedUser(Schema):
    """
    Explanations of limitations:
    nickname — lines with -6 characters are easy to confuse, and lines with 30+ characters are difficult to recognize;
    email — see RFC 3696.
    """

    nickname: Annotated[str, Field(min_length=6, max_length=30, examples=["Ivan Ivanov"])]
    email: Annotated[EmailStr, Field(max_length=256, examples=["ivanov@mail.ru"])]


class UserRead(DBSchema, ExtendedUser, BaseUser):
    pass


class UserCreate(ExtendedUser, BaseUserCreate):
    """
    By default, an example “string” is created for the str type, which is not a secure password even for debugging.
    """

    password: Annotated[str, Field(examples=["-¯#P'Hä¯Nðfº2>+¶;Öðº±í,M»)î¾æd"])]


class UserUpdate(Schema, BaseUserUpdate):
    nickname: Annotated[str | None, Field(min_length=6, max_length=30, examples=["Ivan Ivanov"])] = None
    email: Annotated[EmailStr | None, Field(max_length=256, examples=["ivanov@mail.ru"])] = None
