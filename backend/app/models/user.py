"""
User and Role Models
====================

Defines authentication and authorization entities for AgriFlow.

- **Role**: Named permission groups (e.g., "admin", "operator"). Seeded on
  application startup via the lifespan handler in main.py.
- **User**: Authenticated accounts identified by email. The first user to
  register is automatically promoted to admin.
- **user_roles**: Many-to-many association table linking users to roles.

KNOWN INCONSISTENCY: The User model carries both a direct ``role_id`` FK column
(single-role shortcut) *and* a many-to-many ``roles`` relationship through the
``user_roles`` association table. Some CRUD/router code references ``user.roles``
(the M2M list) while other code uses ``user.role_id``. Additionally, some code
references ``user.username`` which does not exist -- the model uses ``email``
as the login identifier.
"""

from datetime import datetime
from typing import List

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..database import Base


# Many-to-many association table linking users to roles.
# Both FKs use CASCADE on delete so that removing a user or role automatically
# cleans up the join rows.
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey(
        "users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey(
        "roles.id", ondelete="CASCADE"), primary_key=True),
)


class Role(Base):
    """
    Role database model.

    Represents a named permission group (e.g., "admin", "operator", "viewer").
    Roles are seeded at application startup and referenced for route-level
    access control via the ``roles_required`` / ``roles_accepted`` dependencies.
    """

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)  # Role identifier, e.g. "admin"
    description: Mapped[str] = mapped_column(String, nullable=False)  # Human-readable description of the role's permissions

    # Many-to-many back-reference: all users that hold this role
    users: Mapped[List["User"]] = relationship(
        secondary=user_roles,
        back_populates="roles"
    )

    def __repr__(self):
        return f"<Role(name={self.name})>"


class User(Base):
    """
    User database model.

    Represents an authenticated user account in AgriFlow. Users log in with
    their email and password (bcrypt-hashed). The first user to register via
    the public registration endpoint is automatically assigned the "admin" role.

    NOTE: This model has a known dual-role pattern -- see module docstring for
    details on the role_id / roles inconsistency.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)  # Login identifier; no separate "username" field exists
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)  # bcrypt hash produced by app.core.security
    full_name: Mapped[str] = mapped_column(String, nullable=True)  # Display name, optional
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)  # Account activation flag
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)  # Email verification flag
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)  # Direct single-role FK (inconsistent with M2M below)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())  # Account creation timestamp
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )  # Last-modified timestamp, auto-updated

    # Many-to-many relationship to Role via user_roles association table.
    # NOTE: Coexists with the direct role_id FK above. See module docstring.
    roles: Mapped[List["Role"]] = relationship(
        secondary=user_roles,
        back_populates="users"
    )

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, full_name={self.full_name}, roles={self.roles})>"
