from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class BatchBase(BaseModel):
    id: int
    batch_code: str
    plantation_id: int
    stage_id: int
    weight_kg: Decimal
    parent_batch_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class BatchCreate(BatchBase):
    pass


class BatchUpdate(BatchBase):
    pass


class BatchSchema(BatchBase):
    created_at: datetime
    updated_at: datetime
    child_batches: List["BatchSchema"] = []
    transformation_inputs: List["TransformationInputs"] = []
    transformation_outputs: List["TransformationOutputs"] = []

    model_config = ConfigDict(from_attributes=True)
