from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .transformation import Transformation


class Consumable(Base):
    """
    Consumable items - defines the item ONLY.
    NO stock quantity or price stored here!
    """

    __tablename__ = "consumables"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    unit: Mapped[str] = mapped_column(String(50))  # liters, kg, pieces, etc.
    description: Mapped[str | None] = mapped_column(String(500))

    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    purchases: Mapped[List["ConsumablePurchase"]] = relationship(
        back_populates="consumable",
        order_by="ConsumablePurchase.purchase_date",  # Critical for FIFO
    )
    consumptions: Mapped[List["ConsumableConsumption"]] = relationship(
        back_populates="consumable"
    )

    def __repr__(self) -> str:
        return f"<Consumable(id={self.id}, name='{self.name}', unit='{self.unit}')>"


class ConsumablePurchase(Base):
    """
    Tracks each purchase of consumable items.
    Each purchase is a "lot" that will be consumed in FIFO order.
    """

    __tablename__ = "consumable_purchases"

    __table_args__ = (
        Index("idx_consumable_purchase_fifo", "consumable_id", "purchase_date"),
        CheckConstraint("remaining_quantity >= 0", name="check_remaining_positive"),
        CheckConstraint(
            "remaining_quantity <= quantity", name="check_remaining_lte_quantity"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    consumable_id: Mapped[int] = mapped_column(ForeignKey("consumables.id"), index=True)

    purchase_date: Mapped[datetime] = mapped_column(
        index=True
    )  # CRITICAL for FIFO ordering
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2)
    )  # Price at time of purchase (FROZEN)

    # Track remaining quantity for FIFO consumption
    remaining_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    # Optional purchase details
    supplier: Mapped[str | None] = mapped_column(String(200))
    invoice_number: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(String(500))

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationships
    consumable: Mapped["Consumable"] = relationship(back_populates="purchases")
    allocations: Mapped[List["ConsumptionAllocation"]] = relationship(
        back_populates="purchase", cascade="all, delete-orphan"
    )

    @property
    def is_exhausted(self) -> bool:
        """Check if this purchase lot is fully consumed"""
        return self.remaining_quantity <= 0

    @property
    def consumed_quantity(self) -> Decimal:
        """How much has been consumed from this lot"""
        return self.quantity - self.remaining_quantity

    @property
    def total_cost(self) -> Decimal:
        """Total cost of this purchase"""
        return self.quantity * self.unit_cost

    def __repr__(self) -> str:
        return f"<ConsumablePurchase(id={self.id}, item='{self.consumable.name}', date={self.purchase_date.date()}, qty={self.quantity}, remaining={self.remaining_quantity}, cost=₹{self.unit_cost})>"


class ConsumableConsumption(Base):
    """
    Tracks consumption of consumables in transformations.
    Each consumption is allocated to specific purchase lots via ConsumptionAllocation (FIFO).
    """

    __tablename__ = "consumable_consumptions"

    __table_args__ = (
        Index(
            "idx_consumption_transform_consumable", "transformation_id", "consumable_id"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    transformation_id: Mapped[int] = mapped_column(
        ForeignKey("transformations.id"), index=True
    )
    consumable_id: Mapped[int] = mapped_column(ForeignKey("consumables.id"), index=True)

    consumption_date: Mapped[datetime] = mapped_column(index=True)
    quantity_used: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    # Total cost is calculated from allocations and FROZEN
    total_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    notes: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationships
    transformation: Mapped["Transformation"] = relationship(
        back_populates="consumable_consumptions"
    )
    consumable: Mapped["Consumable"] = relationship(back_populates="consumptions")
    allocations: Mapped[List["ConsumptionAllocation"]] = relationship(
        back_populates="consumption", cascade="all, delete-orphan"
    )

    @property
    def average_unit_cost(self) -> Decimal:
        """Average cost per unit for this consumption"""
        if self.quantity_used > 0:
            return self.total_cost / self.quantity_used
        return Decimal("0")

    def __repr__(self) -> str:
        return f"<ConsumableConsumption(id={self.id}, item='{self.consumable.name}', qty={self.quantity_used}, cost=₹{self.total_cost})>"


class ConsumptionAllocation(Base):
    """
    Links a consumption to specific purchase lots (FIFO allocation).
    This is the key to FIFO inventory management.

    Example: Consumption of 30L diesel might be allocated as:
    - 20L from Purchase#1 (bought at ₹100/L on Jan 1)
    - 10L from Purchase#2 (bought at ₹110/L on Jan 15)
    """

    __tablename__ = "consumption_allocations"

    __table_args__ = (
        CheckConstraint("quantity_allocated > 0", name="check_allocation_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    consumption_id: Mapped[int] = mapped_column(
        ForeignKey("consumable_consumptions.id"), index=True
    )
    purchase_id: Mapped[int] = mapped_column(
        ForeignKey("consumable_purchases.id"), index=True
    )

    # How much from this purchase was allocated to this consumption
    quantity_allocated: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    # Cost of this specific allocation (quantity × unit_cost from purchase) - FROZEN
    cost: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationships
    consumption: Mapped["ConsumableConsumption"] = relationship(
        back_populates="allocations"
    )
    purchase: Mapped["ConsumablePurchase"] = relationship(back_populates="allocations")

    def __repr__(self) -> str:
        return f"<ConsumptionAllocation(consumption_id={self.consumption_id}, purchase_id={self.purchase_id}, qty={self.quantity_allocated}, cost=₹{self.cost})>"
