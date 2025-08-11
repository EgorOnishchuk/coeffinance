from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.models import SQLAlchemyIDModel


class SQLAlchemyUser(SQLAlchemyBaseUserTable[int], SQLAlchemyIDModel):  # type: ignore[misc]
    """
    Explanations of limitations:
    nickname — lines longer than 30 characters are difficult to recognize;
    email — see RFC 3696.
    """

    __tablename__ = "users"

    nickname: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)  # type: ignore[assignment]
