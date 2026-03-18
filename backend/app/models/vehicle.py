from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .consumables import Consumable
    from .transformation import Transformation


class Vehicle(Base):
    """Vehicles used in operations"""

    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(50), unique=True)
    vehicle_type: Mapped[str | None] = mapped_column(String(100))

    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    fuel_consumable_id: Mapped[int | None] = mapped_column(
        ForeignKey("consumables.id"), nullable=True
    )

    usage: Mapped[List["TransformationVehicle"]] = relationship(
        back_populates="vehicle"
    )
    fuel_consumable: Mapped[Optional["Consumable"]] = relationship("Consumable")

    def __repr__(self) -> str:
        return f"<Vehicle(id={self.id}, number='{self.number}')>"


class TransformationVehicle(Base):
    """Vehicle usage in a transformation"""

    __tablename__ = "transformation_vehicles"

    # No unique constraint — same vehicle may be assigned multiple times (e.g. multiple shifts)

    id: Mapped[int] = mapped_column(primary_key=True)
    transformation_id: Mapped[int] = mapped_column(
        ForeignKey("transformations.id"), index=True
    )
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), index=True)
    hours_used: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    fuel_qty: Mapped[Decimal] = mapped_column(Numeric(8, 2))

    # Cost tracking (FROZEN at time of usage)
    fuel_cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    consumable_consumption_id: Mapped[int | None] = mapped_column(
        ForeignKey("consumable_consumptions.id", ondelete="SET NULL"), nullable=True
    )

    notes: Mapped[str | None] = mapped_column(String(500))

    transformation: Mapped["Transformation"] = relationship(
        back_populates="vehicle_usage"
    )
    vehicle: Mapped["Vehicle"] = relationship(back_populates="usage")

    def __repr__(self) -> str:
        return f"<TransformationVehicle(vehicle='{self.vehicle.number}', hours={self.hours_used}, fuel_qty={self.fuel_qty})>"
