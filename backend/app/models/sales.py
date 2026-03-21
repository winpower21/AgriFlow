from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import CheckConstraint, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Numeric, String

from ..database import Base

if TYPE_CHECKING:
    from .batch import Batch, BatchStage
    from .customer import Customer
    from .user import User


class Sale(Base):
    """Sales transaction. Allocated to specific batches via SaleAllocation (FIFO or manual)."""

    __tablename__ = "sales"
    __table_args__ = (Index("idx_sale_date", "sale_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)

    sale_date: Mapped[datetime] = mapped_column(index=True)
    quantity_sold: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    selling_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    cost_of_goods_sold: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    stage_id: Mapped[int] = mapped_column(ForeignKey("batch_stages.id"), index=True)

    status: Mapped[str] = mapped_column(String(20), default="COMPLETED", index=True)
    allocation_mode: Mapped[str] = mapped_column(String(10))  # "FIFO" or "MANUAL"

    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    reviewed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(500))

    invoice_number: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(String(500))

    # Payment tracking
    is_paid: Mapped[bool] = mapped_column(default=False)
    payment_method: Mapped[str | None] = mapped_column(String(20), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(nullable=True)
    paid_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer")
    stage: Mapped["BatchStage"] = relationship("BatchStage")
    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_id])
    reviewed_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[reviewed_by_id])
    paid_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[paid_by_id])
    allocations: Mapped[List["SaleAllocation"]] = relationship(
        back_populates="sale", cascade="all, delete-orphan"
    )

    @property
    def unit_selling_price(self) -> Decimal:
        if self.quantity_sold > 0:
            return self.selling_price / self.quantity_sold
        return Decimal("0")

    @property
    def profit(self) -> Decimal:
        return self.selling_price - self.cost_of_goods_sold

    @property
    def profit_margin(self) -> Decimal:
        if self.selling_price > 0:
            return (self.profit / self.selling_price) * 100
        return Decimal("0")

    def __repr__(self) -> str:
        return f"<Sale(id={self.id}, date={self.sale_date.date()}, qty={self.quantity_sold}kg, status={self.status})>"


class SaleAllocation(Base):
    """Links a sale to specific batches (FIFO or manual allocation)."""

    __tablename__ = "sale_allocations"
    __table_args__ = (
        CheckConstraint("quantity_allocated > 0", name="check_sale_allocation_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sale_id: Mapped[int] = mapped_column(ForeignKey("sales.id"), index=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id"), index=True)

    quantity_allocated: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    cost_allocated: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    sale: Mapped["Sale"] = relationship(back_populates="allocations")
    batch: Mapped["Batch"] = relationship(back_populates="sale_allocations")

    def __repr__(self) -> str:
        return f"<SaleAllocation(sale_id={self.sale_id}, batch_id={self.batch_id}, qty={self.quantity_allocated})>"
