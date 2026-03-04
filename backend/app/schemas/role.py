from typing import Optional

from pydantic import BaseModel, ConfigDict


class RoleBase(BaseModel):
    """Base role schema."""
    name: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    """Schema for creating a role."""
    pass


class Role(RoleBase):
    """Schema for role response."""
    id: int

    model_config = ConfigDict(from_attributes=True)
