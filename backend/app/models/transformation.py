"""
Transformation Models
======================

Models the processing events that convert agricultural material from one stage
to another. A **Transformation** is a single processing operation (e.g., cleaning,
drying, grading) that consumes one or more input batches and produces one or more
output batches.

Relationships to resources:
    Each transformation can reference:
    - Personnel assignments (TransformationPersonnel) with frozen wage costs
    - Vehicle usage (TransformationVehicle) with frozen hourly costs
    - Consumable consumption (ConsumableConsumption) with FIFO-allocated costs

The input/output link tables (TransformationInput / TransformationOutput) record
the weight of material consumed or produced, enabling yield-loss tracking across
the processing pipeline.

Unique constraints on (transformation_id, batch_id) in both input and output
tables prevent the same batch from being listed twice in a single transformation.
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import Boolean

from ..database import Base

if TYPE_CHECKING:
    from .batch import Batch
    from .consumables import ConsumableConsumption
    from .expense import Expense
    from .personnel import TransformationPersonnel
    from .transformation import Transformation
    from .vehicle import TransformationVehicle


class TransformationType(Base):
    """
    Types of transformations/processing.

    Defines the category of a transformation event. Common types follow the
    processing pipeline stages:
        HARVEST - Gathering raw material from plantation
        CLEAN   - Removing impurities
        DRY     - Reducing moisture content
        BAG     - Packaging into bulk bags
        GRADE   - Quality sorting (A, B, 555, etc.)
        PACK    - Final retail packaging

    Stored in the database (not an enum) to allow adding new transformation
    types without code changes.
    """

    __tablename__ = "transformation_types"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(100), unique=True
    )  # Type identifier, e.g. "CLEAN", "DRY", "GRADE"
    is_root: Mapped[bool] = mapped_column(Boolean, default=False)
    # transformation_stage_level: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(
        String(1000), nullable=True
    )  # Optional description of what this transformation type involves

    # All transformation events of this type
    transformations: Mapped[List["Transformation"]] = relationship(
        back_populates="transformation_type"
    )


class Transformation(Base):
    """
    Records one processing event.

    A transformation represents a discrete processing operation (e.g., drying
    a batch of harvested material). It spans a time range (from_date to to_date)
    and aggregates all related costs:
        - Input/output material weights (TransformationInput/Output)
        - Labour costs (TransformationPersonnel with frozen rates)
        - Vehicle costs (TransformationVehicle with frozen hourly rates)
        - Consumable costs (ConsumableConsumption with FIFO-allocated purchase costs)

    All child relationships use ``cascade="all, delete-orphan"`` so that deleting
    a transformation automatically removes its associated inputs, outputs, personnel
    assignments, vehicle usage records, and consumable consumption records.
    """

    __tablename__ = "transformations"

    id: Mapped[int] = mapped_column(primary_key=True)
    type_id: Mapped[int] = mapped_column(
        ForeignKey("transformation_types.id")
    )  # FK to TransformationType (e.g., CLEAN, DRY)
    from_date: Mapped[datetime] = mapped_column(
        index=True
    )  # Processing start date; indexed for date-range queries
    to_date: Mapped[datetime | None] = mapped_column(
        index=True, nullable=True
    )  # Processing end date; null means in-progress
    notes: Mapped[str | None] = mapped_column(String(1000))  # Free-text operator notes
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    # Batches consumed by this transformation (material going in)
    inputs: Mapped[List["TransformationInput"]] = relationship(
        back_populates="transformation", cascade="all, delete-orphan"
    )
    # Batches produced by this transformation (material coming out)
    outputs: Mapped[List["TransformationOutput"]] = relationship(
        back_populates="transformation", cascade="all, delete-orphan"
    )
    # Workers assigned to this transformation, with frozen wage data
    personnel_assignments: Mapped[List["TransformationPersonnel"]] = relationship(
        back_populates="transformation", cascade="all, delete-orphan"
    )
    # Vehicles used during this transformation, with frozen cost data
    vehicle_usage: Mapped[List["TransformationVehicle"]] = relationship(
        back_populates="transformation", cascade="all, delete-orphan"
    )
    # Consumables used during this transformation, with FIFO cost allocation
    consumable_consumptions: Mapped[List["ConsumableConsumption"]] = relationship(
        back_populates="transformation", cascade="all, delete-orphan"
    )
    # The type/category of this transformation
    transformation_type: Mapped["TransformationType"] = relationship(
        back_populates="transformations"
    )
    # Expenses linked to this transformation (wages, additional costs)
    expenses: Mapped[List["Expense"]] = relationship(
        "Expense", back_populates="transformation"
    )

    def __repr__(self) -> str:
        type_name = (
            self.transformation_type.name if self.transformation_type else "Unknown"
        )
        return f"<Transformation(id={self.id}, type={type_name}, date={self.date})>"


class TransformationInput(Base):
    """
    Links input batches to a transformation.

    Records how much weight was consumed from a specific batch during a
    transformation. The ``input_weight`` is deducted from the source batch's
    ``remaining_weight_kg``. When the sum of all input weights equals the
    batch's ``initial_weight_kg``, the batch is marked as depleted.

    Constraint: A batch can appear at most once per transformation
    (``uq_transformation_input_batch``).
    """

    __tablename__ = "transformation_inputs"

    # Prevents the same batch from being listed as input twice in one transformation
    __table_args__ = (
        UniqueConstraint(
            "transformation_id", "batch_id", name="uq_transformation_input_batch"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    transformation_id: Mapped[int] = mapped_column(
        ForeignKey("transformations.id"), index=True
    )  # FK to the parent transformation event
    batch_id: Mapped[int] = mapped_column(
        ForeignKey("batches.id"), index=True
    )  # FK to the batch being consumed
    input_weight: Mapped[Decimal] = mapped_column(
        Numeric(10, 2)
    )  # Weight (kg) consumed from this batch in this transformation

    transformation: Mapped["Transformation"] = relationship(back_populates="inputs")
    batch: Mapped["Batch"] = relationship(
        back_populates="transformation_inputs"
    )  # The batch that was consumed

    def __repr__(self) -> str:
        return f"<TransformationInput(transformation_id={self.transformation_id}, batch_id={self.batch_id}, weight={self.input_weight}kg)>"


class TransformationOutput(Base):
    """
    Links output batches to a transformation.

    Records the batches produced by a transformation and their weights. Output
    batches are newly created Batch records at the next processing stage. The
    difference between total input weight and total output weight represents
    processing loss (e.g., moisture loss during drying).

    Constraint: A batch can appear at most once per transformation
    (``uq_transformation_output_batch``).
    """

    __tablename__ = "transformation_outputs"

    # Prevents the same batch from being listed as output twice in one transformation
    __table_args__ = (
        UniqueConstraint(
            "transformation_id", "batch_id", name="uq_transformation_output_batch"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    transformation_id: Mapped[int] = mapped_column(
        ForeignKey("transformations.id"), index=True
    )  # FK to the parent transformation event
    batch_id: Mapped[int] = mapped_column(
        ForeignKey("batches.id"), index=True
    )  # FK to the newly produced batch
    output_weight: Mapped[Decimal] = mapped_column(
        Numeric(10, 2)
    )  # Weight (kg) of material produced in this output batch

    transformation: Mapped["Transformation"] = relationship(back_populates="outputs")
    batch: Mapped["Batch"] = relationship(
        back_populates="transformation_outputs"
    )  # The batch that was produced

    def __repr__(self) -> str:
        return f"<TransformationOutput(transformation_id={self.transformation_id}, batch_id={self.batch_id}, weight={self.output_weight}kg)>"
