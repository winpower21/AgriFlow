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
    __tablename__ = "batch_stages"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    batches: Mapped[List["Batch"]] = relationship("Batch", back_populates="stage")

    def __repr__(self) -> str:
        return f"<BatchStage(id={self.id}, name='{self.name}')>"


class Batch(Base):
    """A batch is any physical quantity of material at any stage"""

    __tablename__ = "batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    plantation_id: Mapped[int | None] = mapped_column(ForeignKey("plantations.id"))
    stage_id: Mapped[int | None] = mapped_column(ForeignKey("batch_stages.id"))
    initial_weight_kg: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    remaining_weight_kg: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    is_depleted: Mapped[bool] = mapped_column(default=False, index=True)
    parent_batch_id: Mapped[int | None] = mapped_column(ForeignKey("batches.id"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
    plantation: Mapped[Optional["Plantation"]] = relationship(back_populates="batches")
    parent_batch: Mapped[Optional["Batch"]] = relationship(
        "Batch", remote_side=[id], back_populates="child_batches"
    )
    child_batches: Mapped[List["Batch"]] = relationship(
        "Batch", back_populates="parent_batch", remote_side=[parent_batch_id]
    )

    transformation_inputs: Mapped[List["TransformationInput"]] = relationship(
        back_populates="batch", cascade="all, delete-orphan"
    )
    transformation_outputs: Mapped[List["TransformationOutput"]] = relationship(
        back_populates="batch", cascade="all, delete-orphan"
    )

    # Retail inventory (for RETAIL stage batches)
    retail_inventory: Mapped[Optional["RetailInventory"]] = relationship(
        back_populates="batch", uselist=False
    )
    stage: Mapped[Optional["BatchStage"]] = relationship(back_populates="batches")

    def __repr__(self) -> str:
        stage_name = self.stage.name if self.stage else "Unknown"
        return f"<Batch(id={self.id}, code='{self.batch_code}', stage={stage_name}, weight={self.weight_kg}kg)>"
