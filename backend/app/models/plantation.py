"""
Plantation and Lease Models
============================

Models the physical crop source locations (plantations) and the history of
lease agreements associated with each plantation.

Domain context:
    A **Plantation** is the origin point for all raw agricultural material in
    AgriFlow. When material is harvested, a Batch is created with a FK back to
    the originating plantation. Each plantation has at most one geographic
    Location (1-to-1) and zero or more PlantationLease records that capture the
    chronological history of lease costs and durations.
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..database import Base

if TYPE_CHECKING:
    from .batch import Batch
    from .location import Location


class Plantation(Base):
    """
    Where material originates.

    Represents a named crop-growing location. Serves as the starting point of
    the batch lineage chain -- all HARVEST-stage batches reference a plantation.
    Expenses can also be optionally attributed to a plantation for cost tracking.
    """

    __tablename__ = "plantations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)

    # FK to geographic location; nullable — plantation may exist before
    # a location is assigned.
    location_id: Mapped[int | None] = mapped_column(
        ForeignKey("locations.id"), nullable=True
    )

    # Area stored in hectares; displayed in UI converted to local unit.
    area_hectares: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 4), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    # All batches harvested from this plantation
    batches: Mapped[List["Batch"]] = relationship(back_populates="plantation")

    # Chronological lease agreements, most recent first
    lease: Mapped[List["PlantationLease"]] = relationship(
        back_populates="plantation", order_by="PlantationLease.start_date.desc()"
    )

    location: Mapped["Location"] = relationship(back_populates="plantations")

    @property
    def is_active(self) -> bool:
        """True if the plantation has a current or open-ended lease.

        A plantation is 'active' when its most recent lease has an end_date
        that is today or in the future, or when end_date is NULL (open-ended).
        Requires the ``lease`` relationship to be loaded (use joinedload).
        """
        from datetime import date
        today = date.today()
        return any(
            l.end_date is None or l.end_date.date() >= today
            for l in self.lease
        )

    def __repr__(self) -> str:
        return f"<Plantation(id={self.id}, name='{self.name}')>"


class PlantationLease(Base):
    """
    History of lease agreements.

    Tracks the lease cost and duration for a plantation over time. Multiple
    lease records per plantation allow capturing renegotiations and renewals
    without losing historical data. The ``cost`` field records the total lease
    amount for the period (not a rate per unit time).
    """

    __tablename__ = "plantation_leases"

    id: Mapped[int] = mapped_column(primary_key=True)
    plantation_id: Mapped[int] = mapped_column(
        ForeignKey("plantations.id")
    )  # FK to the plantation this lease covers
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now()
    )  # Lease creation date
    start_date: Mapped[datetime] = mapped_column()  # Lease period start (inclusive)
    end_date: Mapped[datetime | None] = mapped_column(nullable=True)  # Lease period end (inclusive); nullable for open-ended leases
    cost: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )  # Total lease cost for the period; nullable for pending/unknown

    # Back-reference to the parent plantation
    plantation: Mapped["Plantation"] = relationship(
        "Plantation", back_populates="lease"
    )

    def __repr__(self) -> str:
        return f"<LeaseHistory(plantation_id={self.plantation_id}, start={self.start_date}, end={self.end_date}, cost={self.cost})>"
