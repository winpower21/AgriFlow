from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .plantation import Plantation
    from .transformation import Transformation
    from .vehicle import Vehicle


class ExpenseCategory(Base):
    """Categories for expenses (e.g., 'Fuel', 'Maintenance', 'Rent', 'Utilities')"""

    __tablename__ = "expense_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(500))
    is_system: Mapped[bool] = mapped_column(default=False)

    expenses: Mapped[List["Expense"]] = relationship(back_populates="category")

    def __repr__(self) -> str:
        return f"<ExpenseCategory(name='{self.name}')>"


class Expense(Base):
    """
    General expenses tracking.
    Can be linked to specific assets (Plantation, Vehicle) or general overhead.
    """

    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime] = mapped_column(index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    category_id: Mapped[int] = mapped_column(ForeignKey("expense_categories.id"))

    # Optional links to assets
    plantation_id: Mapped[int | None] = mapped_column(ForeignKey("plantations.id"))
    vehicle_id: Mapped[int | None] = mapped_column(ForeignKey("vehicles.id"))
    transformation_id: Mapped[int | None] = mapped_column(
        ForeignKey("transformations.id", ondelete="SET NULL"), nullable=True
    )

    description: Mapped[str | None] = mapped_column(String(1000))
    receipt_image: Mapped[str | None] = mapped_column(String(500))  # Path to image

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    category: Mapped["ExpenseCategory"] = relationship(back_populates="expenses")
    plantation: Mapped[Optional["Plantation"]] = relationship("Plantation")
    vehicle: Mapped[Optional["Vehicle"]] = relationship("Vehicle")
    transformation: Mapped[Optional["Transformation"]] = relationship(
        "Transformation", back_populates="expenses"
    )

    def __repr__(self) -> str:
        category_name = self.category.name if self.category else "Unknown"
        return (
            f"<Expense(id={self.id}, amount={self.amount}, category='{category_name}')>"
        )
