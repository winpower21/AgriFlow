from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr

from .role import Role


# Shared properties
class UserBase(BaseModel):
    """Base user schema with common fields."""

    email: EmailStr
    full_name: Optional[str] = None


# Properties to receive via API on creation
class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str


# Properties to receive via API on update
class UserUpdate(BaseModel):
    """Schema for updating a user (all fields optional)."""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


class RoleChange(BaseModel):
    """Schema for changing a user's role."""

    role: str


# Properties shared by models stored in DB
class UserInDBBase(UserBase):
    """Schema for user data from database."""

    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# Properties to return to client
class User(UserInDBBase):
    """Schema for user response (what API returns)."""

    roles: List[Role] = []


# Properties stored in DB
class UserInDB(UserInDBBase):
    """Schema for user in database (includes hashed password)."""

    hashed_password: str
