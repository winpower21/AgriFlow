"""
User-related Pydantic schemas.

Defines the request and response models for user registration, profile
updates, role changes, and reading user data from the database.  Follows the
standard Base -> Create / Update / Schema (response) layering pattern.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr

from .role import Role


# ---------------------------------------------------------------------------
# Shared properties
# ---------------------------------------------------------------------------

class UserBase(BaseModel):
    """Base user schema with common fields shared by create and read models.

    Fields:
        email:     The user's unique email address (validated as EmailStr).
        full_name: Optional display name for the user.
    """

    email: EmailStr
    full_name: Optional[str] = None


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------

class UserCreate(UserBase):
    """Request body for creating (registering) a new user.

    Inherits ``email`` and ``full_name`` from UserBase and adds the plaintext
    ``password`` which will be hashed before storage.
    """

    password: str


class UserUpdate(BaseModel):
    """Request body for updating an existing user's profile.

    All fields are optional so that a partial update (PATCH-style) can be
    performed.  ``password``, if provided, will be re-hashed before storage.
    ``is_active`` and ``is_verified`` are admin-level flags.
    """

    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


class RoleChange(BaseModel):
    """Request body for changing a user's role.

    Fields:
        role: The name of the target role (e.g. 'admin', 'manager', 'worker').
    """

    role: str


# ---------------------------------------------------------------------------
# Database / response models
# ---------------------------------------------------------------------------

class UserInDBBase(UserBase):
    """Shared base for models that represent a user record stored in the DB.

    Adds server-managed fields (``id``, timestamps, account flags) on top of
    UserBase.  Enables ORM-mode reading via ``from_attributes = True``.
    """

    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class User(UserInDBBase):
    """API response schema returned to the client when reading user data.

    Extends UserInDBBase with the list of roles assigned to the user.
    The ``hashed_password`` is intentionally excluded for security.
    """

    roles: List[Role] = []


class UserInDB(UserInDBBase):
    """Internal-only schema that includes the hashed password.

    Used for authentication checks within the backend; never serialised
    directly to an API response.
    """

    hashed_password: str
