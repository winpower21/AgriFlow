from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List

from sqlalchemy import CheckConstraint, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Numeric, String

from ..database import Base

if TYPE_CHECKING:
    from .batch import Batch


class RetailInventory(Base):
    """
    Tracks retail-stage batches as inventory available for sale.
    Each retail batch becomes an inventory lot (similar to ConsumablePurchase).
    """

    __tablename__ = "retail_inventory"

    __table_args__ = (
        Index("idx_retail_inventory_fifo", "created_date"),
        CheckConstraint(
            "remaining_quantity >= 0", name="check_retail_remaining_positive"
        ),
        CheckConstraint(
            "remaining_quantity <= quantity", name="check_retail_remaining_lte_quantity"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(
        ForeignKey("batches.id"), unique=True, index=True
    )

    created_date: Mapped[datetime] = mapped_column(
        index=True
    )  # CRITICAL for FIFO ordering
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2))  # Initial quantity (kg)
    remaining_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2))  # Current stock

    # Production cost per kg (from all transformation costs)
    cost_per_kg: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    notes: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    batch: Mapped["Batch"] = relationship(back_populates="retail_inventory")
    sale_allocations: Mapped[List["SaleAllocation"]] = relationship(
        back_populates="inventory", cascade="all, delete-orphan"
    )

    @property
    def is_exhausted(self) -> bool:
        """Check if this inventory lot is fully sold"""
        return self.remaining_quantity <= 0

    @property
    def sold_quantity(self) -> Decimal:
        """How much has been sold from this lot"""
        return self.quantity - self.remaining_quantity

    @property
    def total_cost(self) -> Decimal:
        """Total production cost of this inventory"""
        return self.quantity * self.cost_per_kg

    def __repr__(self) -> str:
        return f"<RetailInventory(id={self.id}, batch='{self.batch.batch_code}', qty={self.quantity}, remaining={self.remaining_quantity}, cost_per_kg=₹{self.cost_per_kg})>"


class Sale(Base):
    """
    Sales transaction.
    Each sale is allocated to specific inventory lots via SaleAllocation (FIFO).
    """

    __tablename__ = "sales"

    __table_args__ = (Index("idx_sale_date", "sale_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)

    sale_date: Mapped[datetime] = mapped_column(index=True)
    quantity_sold: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    # Selling price (total revenue)
    selling_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    # Cost of goods sold (calculated from allocations) - FROZEN
    cost_of_goods_sold: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    # Optional customer info
    customer_name: Mapped[str | None] = mapped_column(String(200))
    customer_phone: Mapped[str | None] = mapped_column(String(20))
    customer_address: Mapped[str | None] = mapped_column(String(500))

    invoice_number: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(String(500))

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationships
    allocations: Mapped[List["SaleAllocation"]] = relationship(
        back_populates="sale", cascade="all, delete-orphan"
    )

    @property
    def unit_selling_price(self) -> Decimal:
        """Selling price per kg"""
        if self.quantity_sold > 0:
            return self.selling_price / self.quantity_sold
        return Decimal("0")

    @property
    def profit(self) -> Decimal:
        """Profit = Revenue - COGS"""
        return self.selling_price - self.cost_of_goods_sold

    @property
    def profit_margin(self) -> Decimal:
        """Profit margin as percentage"""
        if self.selling_price > 0:
            return (self.profit / self.selling_price) * 100
        return Decimal("0")

    def __repr__(self) -> str:
        return f"<Sale(id={self.id}, date={self.sale_date.date()}, qty={self.quantity_sold}kg, price=₹{self.selling_price}, profit=₹{self.profit})>"


class SaleAllocation(Base):
    """
    Links a sale to specific inventory lots (FIFO allocation).
    This is the key to FIFO sales inventory management.

    Example: Sale of 30kg might be allocated as:
    - 20kg from Inventory#1 (batch GA-001, cost ₹100/kg)
    - 10kg from Inventory#2 (batch GA-002, cost ₹105/kg)
    """

    __tablename__ = "sale_allocations"

    __table_args__ = (
        CheckConstraint(
            "quantity_allocated > 0", name="check_sale_allocation_positive"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sale_id: Mapped[int] = mapped_column(ForeignKey("sales.id"), index=True)
    inventory_id: Mapped[int] = mapped_column(
        ForeignKey("retail_inventory.id"), index=True
    )

    # How much from this inventory lot was allocated to this sale
    quantity_allocated: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    # Cost of goods for this specific allocation (quantity × cost_per_kg from inventory) - FROZEN
    cost_allocated: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationships
    sale: Mapped["Sale"] = relationship(back_populates="allocations")
    inventory: Mapped["RetailInventory"] = relationship(
        back_populates="sale_allocations"
    )

    def __repr__(self) -> str:
        return f"<SaleAllocation(sale_id={self.sale_id}, inventory_id={self.inventory_id}, qty={self.quantity_allocated}, cost=₹{self.cost_allocated})>"
