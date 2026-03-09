"""
Batch and BatchStage Models
============================

Core material-tracking models for AgriFlow. Every physical quantity of
agricultural product is represented as a **Batch** at a specific processing
**BatchStage**.

Batch Lineage:
    Batches form a tree structure via the ``parent_batch_id`` self-referencing FK.
    When a transformation consumes an input batch and produces one or more output
    batches, each output batch records its parent. This creates a full genealogy
    from HARVEST through to RETAIL, enabling traceability of any retail product
    back to its plantation of origin.

Processing Pipeline (typical stages):
    HARVEST -> CLEAN -> DRY -> BAG -> GRADE -> PACK -> RETAIL

Weight Tracking:
    Each batch stores both ``initial_weight_kg`` (weight when created) and
    ``remaining_weight_kg`` (current unconsumed weight). As a batch is consumed
    by transformations, ``remaining_weight_kg`` decreases. When fully consumed,
    ``is_depleted`` is set to True.

Historical Note:
    The commented-out ``BatchStage`` Python enum above was the original design
    using hardcoded stages. It was replaced with the database-backed ``BatchStage``
    table to allow configurable stages without code changes.
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .plantation import Plantation
    from .sales import RetailInventory
    from .transformation import TransformationInput, TransformationOutput


# Original hardcoded enum replaced by database-backed BatchStage table below.
# Kept as a reference for the canonical stage names.
# class BatchStage(PyEnum):
#     """Stages a batch can be in"""

#     HARVESTED = "HARVESTED"
#     CLEANED = "CLEANED"
#     DRIED = "DRIED"
#     BAGGED_BULK = "BAGGED_BULK"
#     GRADED_A = "GRADED_A"
#     GRADED_B = "GRADED_B"
#     GRADED_555 = "GRADED_555"
#     RETAIL = "RETAIL"
#     WASTE = "WASTE"


class BatchStage(Base):
    """
    Configurable processing stage definition.

    Replaces the original Python enum to allow stages to be managed via the
    database (e.g., adding new grading tiers) without requiring code deployments.
    Each Batch references exactly one BatchStage to indicate its current
    processing state.
    """

    __tablename__ = "batch_stages"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # Stage label, e.g. "HARVESTED", "GRADED_A", "RETAIL"
    batches: Mapped[List["Batch"]] = relationship(
        "Batch", back_populates="stage"
    )  # All batches currently at this stage

    def __repr__(self) -> str:
        return f"<BatchStage(id={self.id}, name='{self.name}')>"


class Batch(Base):
    """
    A batch is any physical quantity of material at any stage.

    This is the central entity in AgriFlow's material tracking system. A batch
    is created either at harvest (linked to a plantation) or as the output of a
    transformation (linked to a parent batch). Batches are consumed as inputs to
    subsequent transformations or sold at the RETAIL stage.

    Lineage tracking: The ``parent_batch_id`` self-FK creates a tree that traces
    every retail batch back through its full processing history to the original
    plantation harvest.
    """

    __tablename__ = "batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_code: Mapped[str] = mapped_column(
        String(100), unique=True, index=True
    )  # Unique human-readable identifier, e.g. "GA-001"
    plantation_id: Mapped[int | None] = mapped_column(
        ForeignKey("plantations.id")
    )  # Source plantation; set for HARVEST batches, nullable for derived batches
    stage_id: Mapped[int | None] = mapped_column(
        ForeignKey("batch_stages.id")
    )  # Current processing stage (FK to batch_stages)
    initial_weight_kg: Mapped[Decimal] = mapped_column(
        Numeric(10, 2)
    )  # Weight at batch creation; never changes
    remaining_weight_kg: Mapped[Decimal] = mapped_column(
        Numeric(10, 2)
    )  # Current unconsumed weight; decreases as batch is used in transformations
    is_depleted: Mapped[bool] = mapped_column(
        default=False, index=True
    )  # True when remaining_weight_kg reaches 0; indexed for fast filtering of active batches
    parent_batch_id: Mapped[int | None] = mapped_column(
        ForeignKey("batches.id")
    )  # Self-FK for lineage: points to the batch this was derived from
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    # Source plantation (only for HARVEST-stage batches)
    plantation: Mapped[Optional["Plantation"]] = relationship(back_populates="batches")

    # Self-referential relationship: the batch this one was produced from
    parent_batch: Mapped[Optional["Batch"]] = relationship(
        "Batch", remote_side=[id], back_populates="child_batches"
    )
    # Self-referential relationship: batches produced from this one
    child_batches: Mapped[List["Batch"]] = relationship(
        "Batch", back_populates="parent_batch", remote_side=[parent_batch_id]
    )

    # Transformations where this batch was consumed as an input
    transformation_inputs: Mapped[List["TransformationInput"]] = relationship(
        back_populates="batch", cascade="all, delete-orphan"
    )
    # Transformations where this batch was produced as an output
    transformation_outputs: Mapped[List["TransformationOutput"]] = relationship(
        back_populates="batch", cascade="all, delete-orphan"
    )

    # Retail inventory record (1-to-1); only exists for RETAIL-stage batches
    retail_inventory: Mapped[Optional["RetailInventory"]] = relationship(
        back_populates="batch", uselist=False
    )
    # Current processing stage reference
    stage: Mapped[Optional["BatchStage"]] = relationship(back_populates="batches")

    def __repr__(self) -> str:
        stage_name = self.stage.name if self.stage else "Unknown"
        return f"<Batch(id={self.id}, code='{self.batch_code}', stage={stage_name}, weight={self.weight_kg}kg)>"
