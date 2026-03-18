"""
Personnel and Wage Models
==========================

Models workers (personnel), their wage types, and their assignments to
transformations with historical cost freezing.

Historical Cost Freezing Pattern:
    Personnel.current_rate holds the *current* pay rate and can be updated at
    any time. When a worker is assigned to a transformation, the rate at that
    moment is copied into TransformationPersonnel.rate_at_time and the total
    wage is computed and frozen in TransformationPersonnel.wage_paid. This
    ensures that retroactive rate changes do not alter historical cost records.

Wage Calculation:
    - DAILY wage type: wage = rate_at_time * days_worked + additional_payments
    - PER_KG wage type: wage = rate_at_time * output_weight_considered + additional_payments
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .expense import Expense
    from .transformation import Transformation


class WageType(Base):
    """
    Personnel wage calculation types.

    Defines how a worker's pay is calculated. Common types:
        - DAILY:  paid per day worked (rate * days)
        - PER_KG: paid per kilogram of output produced (rate * kg)
    """

    __tablename__ = "wage_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(50), unique=True
    )  # Wage type identifier, e.g. "DAILY", "PER_KG"
    # All personnel currently assigned this wage type
    personnel: Mapped[List["Personnel"]] = relationship(back_populates="wage_type")
    # All transformation assignments that had this wage type at the time of assignment (frozen snapshot)
    transformation_wage_type_at_time: Mapped[List["TransformationPersonnel"]] = (
        relationship(back_populates="wage_type")
    )


class Personnel(Base):
    """
    Workers/staff.

    Stores the CURRENT wage rate which can be freely updated (e.g., annual raises).
    Historical rates are preserved in TransformationPersonnel via the cost freezing
    pattern -- changing ``current_rate`` here does NOT retroactively affect any
    previously recorded transformation assignments.
    """

    __tablename__ = "personnel"

    id: Mapped[int] = mapped_column(primary_key=True)
    photo: Mapped[str | None] = mapped_column(String(500), nullable=True)  # Path to worker's photo
    name: Mapped[str] = mapped_column(String(200))  # Worker's full name
    wage_type_id: Mapped[int] = mapped_column(
        ForeignKey("wage_types.id")
    )  # FK to WageType (DAILY, PER_KG, etc.)
    current_rate: Mapped[Decimal] = mapped_column(
        Numeric(10, 2)
    )  # Current pay rate; mutable -- frozen snapshots are in TransformationPersonnel

    phone: Mapped[str | None] = mapped_column(
        String(20)
    )  # Contact phone number (optional)
    address: Mapped[str | None] = mapped_column(
        String(500)
    )  # Residential address (optional)

    is_active: Mapped[bool] = mapped_column(
        default=True
    )  # Soft-delete / active status flag
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    # All transformation assignments this worker has been involved in
    assignments: Mapped[List["TransformationPersonnel"]] = relationship(
        back_populates="personnel"
    )
    # Current wage type reference
    wage_type: Mapped["WageType"] = relationship(back_populates="personnel")

    def __repr__(self) -> str:
        return f"<Personnel(id={self.id}, name='{self.name}', current_rate={self.current_rate})>"


# class PersonnelWage(Base):
#     id: Mapped[int] = mapped_column(primary_key=True)
#     date_created: Mapped[datetime] = mapped_column(server_default=func.now())
#     personnel_id: Mapped[int] = mapped_column(ForeignKey('personnel.id'))
#     wage_type_id: Mapped[int] = mapped_column(ForeignKey('wage_types.id'))
#     wage_rate: Mapped[float] = mapped_column()


class TransformationPersonnel(Base):
    """
    Personnel assignment to a transformation with frozen historical costs.

    CRITICAL PATTERN -- HISTORICAL COST FREEZING:
        When a worker is assigned to a transformation, the following values are
        copied from the Personnel record and frozen here:
        - ``wage_type_at_time_id``: the wage type at assignment time
        - ``rate_at_time``: the pay rate at assignment time
        - ``wage_paid``: the total computed wage for this assignment

        Even if Personnel.current_rate or Personnel.wage_type_id are later
        updated, these frozen values remain unchanged, preserving accurate
        historical cost accounting.

    Wage calculation depends on wage type:
        - DAILY:  wage_paid = rate_at_time * days_worked + additional_payments
        - PER_KG: wage_paid = rate_at_time * output_weight_considered + additional_payments

    Constraint: A worker can appear at most once per transformation
    (``uq_transformation_personnel``).
    """

    __tablename__ = "transformation_personnel"

    # Prevents the same worker from being assigned twice to the same transformation
    __table_args__ = (
        UniqueConstraint(
            "transformation_id", "personnel_id", name="uq_transformation_personnel"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    transformation_id: Mapped[int] = mapped_column(
        ForeignKey("transformations.id"), index=True
    )  # FK to the transformation this assignment belongs to
    personnel_id: Mapped[int] = mapped_column(
        ForeignKey("personnel.id"), index=True
    )  # FK to the worker

    assignment_date: Mapped[datetime] = mapped_column(
        index=True
    )  # Date the worker was assigned; indexed for date-range queries

    # --- FROZEN VALUES: captured at assignment time, never updated ---
    wage_type_at_time_id: Mapped[int] = mapped_column(
        ForeignKey("wage_types.id")
    )  # Wage type snapshot (may differ from worker's current wage type)
    rate_at_time: Mapped[Decimal] = mapped_column(
        Numeric(10, 2)
    )  # Pay rate snapshot (may differ from worker's current_rate)

    # For DAILY wage type: number of days worked in this transformation
    days_worked: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))

    # For PER_KG wage type: kg of output attributed to this worker for pay calculation
    output_weight_considered: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    additional_payments: Mapped[Decimal] = mapped_column(
        Numeric(10, 2)
    )  # Bonuses, overtime, or other extra payments
    additional_payments_description: Mapped[str | None] = mapped_column(
        String(100)
    )  # Description of what the additional payment covers

    # Wage computation fields
    base_wage: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    total_wages_payable: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    is_paid: Mapped[bool] = mapped_column(default=False)
    expense_id: Mapped[int | None] = mapped_column(
        ForeignKey("expenses.id", ondelete="SET NULL"), nullable=True
    )

    notes: Mapped[str | None] = mapped_column(
        String(500)
    )  # Free-text notes about this assignment
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # The transformation this worker was assigned to
    transformation: Mapped["Transformation"] = relationship(
        back_populates="personnel_assignments"
    )
    # The worker who was assigned
    personnel: Mapped["Personnel"] = relationship(back_populates="assignments")
    # The wage type that was active at the time of this assignment (frozen snapshot)
    wage_type: Mapped[WageType] = relationship(
        back_populates="transformation_wage_type_at_time"
    )
    # Linked expense record for wage payment tracking
    expense: Mapped[Optional["Expense"]] = relationship("Expense")

    def __repr__(self) -> str:
        return f"<TransformationPersonnel(personnel='{self.personnel.name}', rate={self.rate_at_time}, base_wage={self.base_wage})>"
