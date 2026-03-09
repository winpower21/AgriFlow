"""
Batch Pydantic schemas.

A batch represents a discrete quantity of agricultural material at a specific
processing stage (e.g. HARVEST, CLEAN, DRY, BAG, GRADE, PACK, RETAIL).
Batches form a tree via ``parent_batch_id`` to track lineage when material is
split or transformed.  Weight tracking (initial vs. remaining) supports FIFO
costing and depletion accounting.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class BatchBase(BaseModel):
    """Base batch schema with shared fields used by create and read models.

    Fields:
        batch_code:           Unique human-readable identifier for the batch.
        plantation_id:        FK to the plantation where the batch originated
                              (nullable for batches created via transformation).
        stage_id:             FK to the current processing stage of the batch
                              (references the BatchStage settings entity).
        initial_weight_kg:    Weight in kilograms when the batch was first created.
        remaining_weight_kg:  Current remaining weight after consumption or
                              transformation allocations.
        parent_batch_id:      Self-referencing FK to the parent batch; used to
                              build the material lineage tree.
    """
    batch_code: str
    plantation_id: Optional[int] = None
    stage_id: Optional[int] = None
    initial_weight_kg: Decimal
    remaining_weight_kg: Decimal
    parent_batch_id: Optional[int] = None


class BatchCreate(BatchBase):
    """Request body for creating a new batch.

    Inherits all fields from BatchBase. The ``id``, ``is_depleted``, and
    timestamps are generated server-side.
    """
    pass


class BatchUpdate(BaseModel):
    """Request body for updating an existing batch (PATCH-style).

    All fields are optional; only supplied fields are modified.

    Fields:
        is_depleted: When set to True the batch is marked as fully consumed.
    """
    plantation_id: Optional[int] = None
    stage_id: Optional[int] = None
    remaining_weight_kg: Optional[Decimal] = None
    is_depleted: Optional[bool] = None


class BatchSchema(BatchBase):
    """API response schema for a batch record.

    Extends BatchBase with server-managed fields and a recursive list of
    ``child_batches`` to represent the full material lineage tree in a single
    response.
    """
    id: int
    # Indicates whether all material in this batch has been consumed.
    is_depleted: bool
    created_at: datetime
    updated_at: datetime
    # Recursive children: batches derived from this batch via transformation.
    child_batches: List["BatchSchema"] = []

    model_config = ConfigDict(from_attributes=True)
