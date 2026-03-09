"""
User CRUD service module.

Provides ``UserService``, which encapsulates all database operations related
to user accounts, authentication, and role management.

Key design decisions:
  - **First-user-as-admin pattern**: The router layer calls ``get_user_count()``
    to detect an empty user table and delegates to ``create_admin_user()``
    instead of ``create_user()`` for the very first registration, ensuring
    the system always has at least one admin.
  - **Dual role tracking**: Each user carries both a scalar ``role_id`` FK
    (for quick lookups) and a many-to-many ``roles`` relationship (for
    flexibility). ``change_user_role()`` keeps both in sync.
  - **Password hashing**: Plaintext passwords are hashed via bcrypt
    (``get_password_hash``) before storage. The raw password never reaches
    the database.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from ..core.security import (
    get_password_hash,
    verify_password,
)
from ..models import Role, User
from ..schemas import User as UserSchema
from ..schemas import UserCreate, UserUpdate


class UserService:
    """Service class for user-related database operations.

    Follows the service-object pattern: instantiate with a SQLAlchemy
    ``Session`` (typically via FastAPI's ``get_db`` dependency), then
    call methods to query or mutate user records.

    Attributes:
        db: The active SQLAlchemy session used for all queries.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_user(self, user_id: int) -> Optional[UserSchema]:
        """Get a user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str) -> Optional[UserSchema]:
        """Get a user by email.

        Email is the unique login identifier in AgriFlow (no separate
        username field exists on the User model).
        """
        return self.db.query(User).filter(User.email == email).first()

    def get_users(self, skip: int = 0, limit: int = 100) -> List[UserSchema]:
        """Get a list of users with pagination."""
        return self.db.query(User).offset(skip).limit(limit).all()

    def get_user_count(self) -> int:
        """Get the total number of users.

        Used by the registration endpoint to implement the
        first-user-as-admin pattern: when count is 0 the caller
        promotes the new user to admin automatically.
        """
        return self.db.query(User).count()

    def get_user_roles(self, user_or_id: int | User) -> List[str]:
        """Get a list of role names for a user.

        Accepts either a user ID (int) or a User ORM instance.
        If a User object is passed, the roles relationship is read
        directly without an extra DB query.
        """
        if isinstance(user_or_id, User):
            return [role.name for role in user_or_id.roles]

        user = self.get_user(user_or_id)
        if user:
            return [role.name for role in user.roles]
        return []

    def get_unverified_users(self) -> List[UserSchema]:
        """Get a list of unverified users, ordered by ID.

        Note: Uses Python ``not`` on the column attribute, which may not
        produce the intended SQL filter. Consider ``User.is_verified == False``
        for a correct SQLAlchemy boolean filter.
        """
        return self.db.query(User).filter(not User.is_verified).order_by(User.id).all()

    def create_user(self, user: UserCreate) -> UserSchema:
        """Create a new user with the default 'user' role.

        Steps:
          1. Hash the plaintext password with bcrypt.
          2. Look up the 'user' Role record.
          3. Create the User ORM object with role_id set (scalar FK).
          4. Also append the role to the many-to-many ``roles`` list.
          5. Commit and return the refreshed user.
        """
        print(f"DEBUG: Password length: {len(user.password)}")
        hashed_password = get_password_hash(user.password)
        # Fetch the default 'user' role — seeded at application startup
        default_role = self.db.query(Role).filter(Role.name == "user").first()
        db_user = User(
            email=user.email,
            full_name=user.full_name,
            hashed_password=hashed_password,
            role_id=default_role.id,
        )
        if default_role:
            # Append to many-to-many relationship for role-based access checks
            db_user.roles.append(default_role)

        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def create_admin_user(self, user: UserCreate) -> UserSchema:
        """Create a new admin user — used for the first-user-as-admin pattern.

        When the system has zero registered users, this method is called
        instead of ``create_user()`` so the first account is automatically
        granted the 'admin' role and set as active (``is_active=True``),
        bypassing any verification step.
        """
        print(f"DEBUG: Password length: {len(user.password)}")
        hashed_password = get_password_hash(user.password)
        # Fetch the 'admin' role — seeded at application startup
        default_role = self.db.query(Role).filter(Role.name == "admin").first()
        db_user = User(
            email=user.email,
            hashed_password=hashed_password,
            full_name=user.full_name,
            is_active=True,
            role_id=default_role.id,
        )
        if default_role:
            # Append to many-to-many relationship for role-based access checks
            db_user.roles.append(default_role)

        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def update_user(self, user_id: int, user: UserUpdate) -> Optional[UserSchema]:
        """Update a user's mutable fields.

        Only fields explicitly set in the ``UserUpdate`` payload are
        applied (``exclude_unset=True``). If the payload includes a
        ``password`` field, it is hashed before storage and mapped to
        the ``hashed_password`` column.
        """
        db_user = self.get_user(user_id)
        if not db_user:
            return None

        update_data = user.model_dump(exclude_unset=True)

        # Hash password if it's being updated
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(
                update_data.pop("password")
            )

        for field, value in update_data.items():
            setattr(db_user, field, value)

        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def delete_user(self, user_id: int) -> bool:
        """Delete a user by ID. Returns True on success, False if not found."""
        db_user = self.get_user(user_id)
        if not db_user:
            return False

        self.db.delete(db_user)
        self.db.commit()
        return True

    def change_user_role(self, user_id: int, role_name: str):
        """Change a user's role by replacing their current roles with the new one.

        Updates both the many-to-many ``roles`` list (replaced entirely)
        and the scalar ``role_id`` FK so both representations stay in sync.
        Returns the updated User, or None if the user or role is not found.
        """
        db_user = self.get_user(user_id)
        if not db_user:
            return None
        new_role = self.db.query(Role).filter(Role.name == role_name).first()
        if not new_role:
            return None
        # Replace the entire roles list (many-to-many) with a single-element list
        db_user.roles = [new_role]
        # Also keep the scalar FK in sync
        db_user.role_id = new_role.id
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def authenticate_user(self, email: str, password: str) -> Optional[UserSchema]:
        """Authenticate a user by email and plaintext password.

        Looks up the user by email, then verifies the provided plaintext
        password against the stored bcrypt hash. Returns the User object
        on success or None on failure (wrong email or wrong password).
        """
        print(
            f"DEBUG: Authenticating user with email: {email} and password length: {len(password)}"
        )
        user = self.get_user_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
