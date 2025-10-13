# pyright: reportUninitializedInstanceVariable=false

from decimal import Decimal

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.analytics.schemas import Deviation
from src.core.db.models import SQLAlchemyIDModel, get_length_constraint


class SQLAlchemyRatio(SQLAlchemyIDModel):
    __tablename__ = "ratios"

    name: Mapped[str] = mapped_column(String(20))
    value: Mapped[Decimal]
    deviation: Mapped[Deviation | None]

    analytics_id: Mapped[int] = mapped_column(
        ForeignKey(
            "analytics.id",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
    )

    __table_args__ = (get_length_constraint(name, min_=1, name="name_min_len"),)


class SQLAlchemyAnalytics(SQLAlchemyIDModel):
    __tablename__ = "analytics"

    name: Mapped[str] = mapped_column(String(30))
    ratios: Mapped[list[SQLAlchemyRatio]] = relationship(
        SQLAlchemyRatio,
        cascade="all, delete-orphan",
    )

    company_id: Mapped[int] = mapped_column(
        ForeignKey(
            "companies.id",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
    )

    __table_args__ = (get_length_constraint(name, min_=1, name="name_min_len"),)
