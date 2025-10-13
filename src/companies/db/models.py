# pyright: reportImportCycles=false
# ruff: noqa: PLR2004 # Docs for columns eliminate magic constants.

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from decimal import Decimal  # noqa: TC003
from enum import StrEnum
from types import MappingProxyType
from typing import TYPE_CHECKING, Final, cast

from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKey,
    Numeric,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy import Enum as SQL_Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.analytics.db.models import SQLAlchemyAnalytics
from src.companies.schemas import Countries
from src.core.db.models import (
    SQLAlchemyIDModel,
    SQLAlchemyModel,
    UTCDateTime,
    get_length_constraint,
    utcnow,
)

if TYPE_CHECKING:
    from src.users.db.models import SQLAlchemyUser

companies_users: Final = Table(
    "companies_users",
    SQLAlchemyModel.metadata,
    Column(
        "companies",
        ForeignKey(
            "companies.id",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
    Column(
        "users",
        ForeignKey(
            "users.id",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
)


class SQLAlchemyCompany(SQLAlchemyIDModel):
    __tablename__ = "companies"
    docs: MappingProxyType[str, str] = MappingProxyType(
        {
            "brn": "Stands for business registration number — a unique "
            "identifier assigned to a company by the government.",
            "score": "Average financial rating across all analytical reports.",
        }
    )

    name: Mapped[str] = mapped_column(String(300))
    brn: Mapped[str] = mapped_column(
        String(100),
        doc=docs["brn"],
        comment=docs["brn"],
    )
    country: Mapped[Countries] = mapped_column(  # pyright: ignore[reportInvalidTypeForm] Pyright does not support functional enums: https://github.com/microsoft/pyright/issues/6703.
        SQL_Enum(
            cast(type[StrEnum], Countries),
            values_callable=lambda enum: [str(field) for field in enum],
        )
    )
    score: Mapped[Decimal | None] = mapped_column(
        Numeric(
            precision=8,
            scale=5,
        ),
        doc=docs["score"],
        comment=docs["score"],
    )
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        server_default=utcnow(),
    )

    analytics: Mapped[list[SQLAlchemyAnalytics]] = relationship(
        SQLAlchemyAnalytics,
        cascade="all, delete-orphan",
    )
    users: Mapped[list[SQLAlchemyUser]] = relationship(
        "SQLAlchemyUser",
        secondary=companies_users,
        back_populates="companies",
    )

    __table_args__ = (
        UniqueConstraint(brn, country),
        get_length_constraint(name, min_=1, name="name_min_len"),
        get_length_constraint(brn, min_=1, name="brn_min_len"),
        CheckConstraint(score.between(0, 100), name="score_range"),
    )
