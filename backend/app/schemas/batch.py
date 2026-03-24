"""
Batch Pydantic schemas.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class BatchStageSchema(BaseModel):
    id: int
    name: str
    batch_stage_level: int
    parent_id: int | None = None
    sort_order: int = 0
    icon: str | None = None
    color: str | None = None
    is_waste: bool = False
    model_config = ConfigDict(from_attributes=True)


class BatchBase(BaseModel):
    batch_code: str
    plantation_id: Optional[int] = None
    stage_id: Optional[int] = None
    initial_weight_kg: Decimal
    remaining_weight_kg: Decimal
    notes: Optional[str] = None


class BatchCreate(BatchBase):
    pass


class BatchUpdate(BaseModel):
    """Only allows editing notes and plantation_id after creation."""

    notes: Optional[str] = None
    plantation_id: Optional[int] = None


class BatchSchema(BatchBase):
    id: int
    is_depleted: bool
    created_at: datetime
    updated_at: datetime
    child_batches: List["BatchSchema"] = []
    model_config = ConfigDict(from_attributes=True)


class BatchListItem(BaseModel):
    """Lightweight schema for list views."""

    id: int
    batch_code: str
    plantation_id: Optional[int] = None
    plantation_name: Optional[str] = None
    stage_id: Optional[int] = None
    stage_name: Optional[str] = None
    initial_weight_kg: Decimal
    remaining_weight_kg: Decimal
    is_depleted: bool
    notes: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class BatchDetail(BaseModel):
    """Full detail schema including enriched data."""

    id: int
    batch_code: str
    plantation_id: Optional[int] = None
    plantation_name: Optional[str] = None
    stage_id: Optional[int] = None
    stage_name: Optional[str] = None
    initial_weight_kg: Decimal
    remaining_weight_kg: Decimal
    is_depleted: bool
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class BatchGenealogyNode(BaseModel):
    batch_id: int
    batch_code: str
    stage_name: Optional[str] = None
    remaining_weight_kg: Decimal
    is_depleted: bool
    is_waste: bool = False
    parents: List["BatchGenealogyNode"] = []
    children: List["BatchGenealogyNode"] = []
    model_config = ConfigDict(from_attributes=True)
