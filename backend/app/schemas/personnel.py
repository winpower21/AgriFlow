from decimal import Decimal
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class WageTypeSchema(BaseModel):
    """Schema for wage type response."""

    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class PersonnelBase(BaseModel):
    """Base personnel schema with shared fields."""

    name: str
    wage_type_id: int
    current_rate: Decimal
    phone: Optional[str] = None
    address: Optional[str] = None


class PersonnelCreate(PersonnelBase):
    """Schema for creating personnel."""

    pass


class PersonnelUpdate(BaseModel):
    """Schema for updating personnel. All fields optional."""

    name: Optional[str] = None
    wage_type_id: Optional[int] = None
    current_rate: Optional[Decimal] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None


class PersonnelSchema(PersonnelBase):
    """Schema for personnel response."""

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    wage_type: WageTypeSchema

    model_config = ConfigDict(from_attributes=True)
