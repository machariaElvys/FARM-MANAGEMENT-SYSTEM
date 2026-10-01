from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


def new_id() -> str:
    return str(uuid4())


class User(Base):
    __tablename__ = "farmers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="farmer", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    records: Mapped[list["FarmRecord"]] = relationship(back_populates="farmer", cascade="all, delete-orphan")


class RecordCategory(Base):
    __tablename__ = "record_categories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(60), nullable=False)
    sort_order: Mapped[int] = mapped_column(default=0, nullable=False)

    records: Mapped[list["FarmRecord"]] = relationship(back_populates="category")


class FarmRecord(Base):
    __tablename__ = "farm_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    farmer_id: Mapped[str] = mapped_column(ForeignKey("farmers.id", ondelete="CASCADE"), index=True, nullable=False)
    category_id: Mapped[str] = mapped_column(ForeignKey("record_categories.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    occurred_on: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    unit: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    farmer: Mapped[User] = relationship(back_populates="records")
    category: Mapped[RecordCategory] = relationship(back_populates="records")
