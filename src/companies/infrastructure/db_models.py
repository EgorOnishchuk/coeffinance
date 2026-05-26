# pyright: reportImportCycles=false
# ruff: noqa: PLR2004 # Docs for columns eliminate magic constants.
from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Final, get_args

from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKey,
    Numeric,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    MappedColumn,
    Relationship,
    mapped_column,
    relationship,
)

from src.companies.schemas import Country
from src.core.infrastructure.db_models import (
    SQLAlchemyIDModel,
    SQLAlchemyModel,
    UTCDateTime,
    get_length_constraint,
    utcnow,
)
from src.reports.infrastructure.db_models import SQLAlchemyReport

if TYPE_CHECKING:
    from src.users.infrastructure.db_models import SQLAlchemyUser

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
    docs: Mapping[str, str] = {
        "brn": "Stands for business registration number — a unique "
        "identifier assigned to a company by the government.",
        "score": "Average financial rating across all analytical reports.",
    }

    name: MappedColumn[str] = mapped_column(String(300))
    brn: MappedColumn[str] = mapped_column(
        String(100),
        doc=docs["brn"],
        comment=docs["brn"],
    )
    country: MappedColumn[Country] = mapped_column(
        String(100),
    )
    score: MappedColumn[Decimal | None] = mapped_column(
        Numeric(
            precision=8,
            scale=5,
        ),
        doc=docs["score"],
        comment=docs["score"],
    )
    created_at: MappedColumn[datetime] = mapped_column(
        UTCDateTime(),
        server_default=utcnow(),
    )

    reports: Relationship[list[SQLAlchemyReport]] = relationship(
        SQLAlchemyReport,
        cascade="all, delete-orphan",
        order_by=SQLAlchemyReport.name,
    )
    users: Relationship[list["SQLAlchemyUser"]] = relationship(
        "SQLAlchemyUser",
        secondary=companies_users,
        back_populates="companies",
        order_by="SQLAlchemyUser.nickname",
    )

    __table_args__ = (
        UniqueConstraint(brn, country),
        get_length_constraint(name, min_=1),
        get_length_constraint(brn, min_=1),
        CheckConstraint(score.between(0, 100), name="score_range"),
        CheckConstraint(country.in_(get_args(Country)), name="is_country"),
    )
