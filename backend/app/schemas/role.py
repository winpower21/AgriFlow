"""
Role-related Pydantic schemas.

Defines request and response models for the RBAC (role-based access control)
roles used across the application (e.g. 'admin', 'manager', 'worker').
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict


class RoleBase(BaseModel):
    """Base role schema containing the shared fields.

    Fields:
        name:        Unique role identifier (e.g. 'admin', 'manager').
        description: Optional human-readable explanation of the role's
                     permissions and purpose.
    """
    name: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    """Request body for creating a new role.

    Inherits all fields from RoleBase with no additions; the ``id`` is
    generated server-side.
    """
    pass


class Role(RoleBase):
    """API response schema returned when reading role data.

    Adds the server-generated ``id`` primary key and enables ORM-mode
    reading via ``from_attributes = True``.
    """
    id: int

    model_config = ConfigDict(from_attributes=True)
