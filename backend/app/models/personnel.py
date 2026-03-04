from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .transformation import Transformation


class WageType(Base):
    """Personnel wage calculation types"""

    __tablename__ = "wage_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    personnel: Mapped[List["Personnel"]] = relationship(back_populates="wage_type")
    transformation_wage_type_at_time: Mapped[List["TransformationPersonnel"]] = relationship(back_populates="wage_type")




class Personnel(Base):
    """
    Workers/staff.
    Stores CURRENT wage rate which can be updated.
    Historical rates are preserved in TransformationPersonnel.
    """

    __tablename__ = "personnel"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    wage_type_id: Mapped[int] = mapped_column(ForeignKey("wage_types.id"))
    current_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2))  # Can be updated

    phone: Mapped[str | None] = mapped_column(String(20))
    address: Mapped[str | None] = mapped_column(String(500))

    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    assignments: Mapped[List["TransformationPersonnel"]] = relationship(
        back_populates="personnel"
    )
    wage_type: Mapped["WageType"] = relationship(back_populates="personnel")

    def __repr__(self) -> str:
        return f"<Personnel(id={self.id}, name='{self.name}', current_rate={self.current_rate})>"


class TransformationPersonnel(Base):
    """
    Personnel assignment to transformation.
    CRITICAL: Stores rate_at_time and wage_paid to preserve historical costs.
    Even if current_rate changes in Personnel table, these values remain frozen.
    """

    __tablename__ = "transformation_personnel"

    __table_args__ = (
        UniqueConstraint(
            "transformation_id", "personnel_id", name="uq_transformation_personnel"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    transformation_id: Mapped[int] = mapped_column(
        ForeignKey("transformations.id"), index=True
    )
    personnel_id: Mapped[int] = mapped_column(ForeignKey("personnel.id"), index=True)

    assignment_date: Mapped[datetime] = mapped_column(index=True)

    # FROZEN VALUES - never change even if Personnel.current_rate changes
    wage_type_at_time_id: Mapped[int] = mapped_column(ForeignKey("wage_types.id"))
    rate_at_time: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    # For DAILY wage type
    days_worked: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))

    # For PER_KG wage type
    output_weight_considered: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    additional_payments: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    additional_payments_description: Mapped[str | None] = mapped_column(String(100))

    # Total wage paid (frozen)
    wage_paid: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    notes: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    transformation: Mapped["Transformation"] = relationship(
        back_populates="personnel_assignments"
    )
    personnel: Mapped["Personnel"] = relationship(back_populates="assignments")
    wage_type: Mapped[WageType] = relationship(back_populates="transformation_wage_type_at_time")

    def __repr__(self) -> str:
        return f"<TransformationPersonnel(personnel='{self.personnel.name}', rate={self.rate_at_time}, wage={self.wage_paid})>"
