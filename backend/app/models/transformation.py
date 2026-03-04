from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .batch import Batch
    from .consumables import ConsumableConsumption
    from .personnel import TransformationPersonnel
    from .transformation import Transformation
    from .vehicle import TransformationVehicle


class TransformationType(Base):
    """Types of transformations/processing
    HARVEST
    CLEAN
    DRY
    BAG
    GRADE
    PACK
    """

    __tablename__ = "transformation_types"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str] = mapped_column(String(1000), nullable=True)

    transformations: Mapped[List["Transformation"]] = relationship(
        back_populates="transformation_type"
    )


class Transformation(Base):
    """Records one processing event"""

    __tablename__ = "transformations"

    id: Mapped[int] = mapped_column(primary_key=True)
    type_id: Mapped[int] = mapped_column(ForeignKey("transformation_types.id"))
    from_date: Mapped[datetime] = mapped_column(index=True)
    to_date: Mapped[datetime] = mapped_column(index=True)
    notes: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    inputs: Mapped[List["TransformationInput"]] = relationship(
        back_populates="transformation", cascade="all, delete-orphan"
    )
    outputs: Mapped[List["TransformationOutput"]] = relationship(
        back_populates="transformation", cascade="all, delete-orphan"
    )
    personnel_assignments: Mapped[List["TransformationPersonnel"]] = relationship(
        back_populates="transformation", cascade="all, delete-orphan"
    )
    vehicle_usage: Mapped[List["TransformationVehicle"]] = relationship(
        back_populates="transformation", cascade="all, delete-orphan"
    )
    consumable_consumptions: Mapped[List["ConsumableConsumption"]] = relationship(
        back_populates="transformation", cascade="all, delete-orphan"
    )
    transformation_type: Mapped["TransformationType"] = relationship(
        back_populates="transformations"
    )

    def __repr__(self) -> str:
        type_name = (
            self.transformation_type.name if self.transformation_type else "Unknown"
        )
        return f"<Transformation(id={self.id}, type={type_name}, date={self.date})>"


class TransformationInput(Base):
    """Links input batches to a transformation"""

    __tablename__ = "transformation_inputs"

    __table_args__ = (
        UniqueConstraint(
            "transformation_id", "batch_id", name="uq_transformation_input_batch"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    transformation_id: Mapped[int] = mapped_column(
        ForeignKey("transformations.id"), index=True
    )
    batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id"), index=True)
    input_weight: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    transformation: Mapped["Transformation"] = relationship(back_populates="inputs")
    batch: Mapped["Batch"] = relationship(back_populates="transformation_inputs")

    def __repr__(self) -> str:
        return f"<TransformationInput(transformation_id={self.transformation_id}, batch_id={self.batch_id}, weight={self.input_weight}kg)>"


class TransformationOutput(Base):
    """Links output batches to a transformation"""

    __tablename__ = "transformation_outputs"

    __table_args__ = (
        UniqueConstraint(
            "transformation_id", "batch_id", name="uq_transformation_output_batch"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    transformation_id: Mapped[int] = mapped_column(
        ForeignKey("transformations.id"), index=True
    )
    batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id"), index=True)
    output_weight: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    transformation: Mapped["Transformation"] = relationship(back_populates="outputs")
    batch: Mapped["Batch"] = relationship(back_populates="transformation_outputs")

    def __repr__(self) -> str:
        return f"<TransformationOutput(transformation_id={self.transformation_id}, batch_id={self.batch_id}, weight={self.output_weight}kg)>"
