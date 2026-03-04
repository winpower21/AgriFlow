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
    """Where material originates"""

    __tablename__ = "plantations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    batches: Mapped[List["Batch"]] = relationship(back_populates="plantation")
    location: Mapped["Location"] = relationship(
        "Location", back_populates="plantation", uselist=False
    )
    lease: Mapped[List["PlantationLease"]] = relationship(
        back_populates="plantation",
        order_by="PlantationLease.start_date.desc()",
    )

    def __repr__(self) -> str:
        return f"<Plantation(id={self.id}, name='{self.name}')>"


class PlantationLease(Base):
    """History of lease agreements"""

    __tablename__ = "plantation_leases"

    id: Mapped[int] = mapped_column(primary_key=True)
    plantation_id: Mapped[int] = mapped_column(ForeignKey("plantations.id"))
    start_date: Mapped[datetime] = mapped_column()
    end_date: Mapped[datetime] = mapped_column()
    cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    plantation: Mapped["Plantation"] = relationship(
        "Plantation", back_populates="lease"
    )

    def __repr__(self) -> str:
        return f"<LeaseHistory(plantation_id={self.plantation_id}, start={self.start_date}, end={self.end_date}, cost={self.cost})>"
