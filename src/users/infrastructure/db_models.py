# ruff: noqa: PLR2004 # Docs for columns eliminate magic constants.

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from fastapi_users.models import UserProtocol
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable
from sqlalchemy import String
from sqlalchemy.orm import (
    MappedColumn,
    Relationship,
    mapped_column,
    relationship,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from src.companies.infrastructure.db_models import SQLAlchemyCompany
from src.core.infrastructure.db_models import (
    SQLAlchemyIDModel,
    get_length_constraint,
)


class DBUserProtocol(UserProtocol[int], Protocol):
    nickname: str


class SQLAlchemyUser(SQLAlchemyBaseUserTable[int], SQLAlchemyIDModel):
    __tablename__ = "users"

    docs: Mapping[str, str] = {
        "nickname": "Lines shorter than 6 characters are easy to confuse, "
        "and lines longer than 30 are difficult to recognize.",
        "email": "See RFC 3696 for max length. The theoretical minimum "
        "length is single-character name and domain + @.",
    }

    if TYPE_CHECKING:
        id: int  # type: ignore[assignment] # pyright: ignore[reportIncompatibleVariableOverride] # The lib typing specifics.
        nickname: str  # pyright: ignore[reportUninitializedInstanceVariable]
        email: str
        hashed_password: str
        is_active: bool
        is_superuser: bool
        is_verified: bool
    else:
        nickname: MappedColumn[str] = mapped_column(
            String(30),
            unique=True,
            doc=docs["nickname"],
            comment=docs["nickname"],
        )
        email: MappedColumn[str] = mapped_column(  # type: ignore[assignment]  # pyright: ignore[reportIncompatibleVariableOverride] # Specifics of using type-checking blocks in the lib. Does not affect anything in runtime.
            String(254),
            unique=True,
            doc=docs["email"],
            comment=docs["email"],
        )
        companies: Relationship[list[SQLAlchemyCompany]] = relationship(
            "SQLAlchemyCompany",
            secondary="companies_users",
            back_populates="users",
            order_by="SQLAlchemyCompany.name",
        )

        __table_args__ = (
            get_length_constraint(nickname, min_=6),
            get_length_constraint(email, min_=3),
        )
