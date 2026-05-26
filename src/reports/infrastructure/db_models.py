from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import (
    MappedColumn,
    Relationship,
    mapped_column,
    relationship,
)

from src.core.infrastructure.db_models import (
    SQLAlchemyIDModel,
    SQLAlchemyModel,
    get_length_constraint,
)
from src.reports.schemas import Deviation


class SQLAlchemyRatio(SQLAlchemyModel):
    __tablename__ = "ratios"

    name: MappedColumn[str] = mapped_column(
        String(20),
        primary_key=True,
    )
    value: MappedColumn[Decimal] = mapped_column()
    deviation: MappedColumn[Deviation | None] = mapped_column()

    report_id: MappedColumn[int] = mapped_column(
        ForeignKey(
            "reports.id",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    __table_args__ = (get_length_constraint(name, min_=1),)


class SQLAlchemyReport(SQLAlchemyIDModel):
    __tablename__ = "reports"

    name: MappedColumn[str] = mapped_column(String(30))
    period_start: MappedColumn[date] = mapped_column()
    period_end: MappedColumn[date] = mapped_column()

    ratios: Relationship[list[SQLAlchemyRatio]] = relationship(
        SQLAlchemyRatio,
        cascade="all, delete-orphan",
        order_by=SQLAlchemyRatio.name,
    )
    company_id: MappedColumn[int] = mapped_column(
        ForeignKey(
            "companies.id",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
    )

    __table_args__ = (
        get_length_constraint(name, min_=1),
        CheckConstraint(period_end > period_start, name="period"),
    )
