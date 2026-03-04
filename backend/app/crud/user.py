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
    def __init__(self, db: Session):
        self.db = db

    def get_user(self, user_id: int) -> Optional[UserSchema]:
        """Get a user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str) -> Optional[UserSchema]:
        """Get a user by email."""
        return self.db.query(User).filter(User.email == email).first()

    def get_users(self, skip: int = 0, limit: int = 100) -> List[UserSchema]:
        """Get a list of users with pagination."""
        return self.db.query(User).offset(skip).limit(limit).all()

    def get_user_count(self) -> int:
        """Get the total number of users."""
        return self.db.query(User).count()

    def get_user_roles(self, user_or_id: int | User) -> List[str]:
        """Get a list of roles for a user (accepts user_id or User object)."""
        if isinstance(user_or_id, User):
            return [role.name for role in user_or_id.roles]

        user = self.get_user(user_or_id)
        if user:
            return [role.name for role in user.roles]
        return []

    def get_unverified_users(self) -> List[UserSchema]:
        """Get a list of unverified users."""
        return self.db.query(User).filter(not User.is_verified).order_by(User.id).all()

    def create_user(self, user: UserCreate) -> UserSchema:
        """Create a new user."""
        print(f"DEBUG: Password length: {len(user.password)}")
        hashed_password = get_password_hash(user.password)
        default_role = self.db.query(Role).filter(Role.name == "user").first()
        db_user = User(
            email=user.email,
            full_name=user.full_name,
            hashed_password=hashed_password,
            role_id=default_role.id,
        )
        if default_role:
            db_user.roles.append(default_role)

        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def create_admin_user(self, user: UserCreate) -> UserSchema:
        """Create a new admin user if there are no users."""
        print(f"DEBUG: Password length: {len(user.password)}")
        hashed_password = get_password_hash(user.password)
        default_role = self.db.query(Role).filter(Role.name == "admin").first()
        db_user = User(
            email=user.email,
            hashed_password=hashed_password,
            full_name=user.full_name,
            is_active=True,
            role_id=default_role.id,
        )
        if default_role:
            db_user.roles.append(default_role)

        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def update_user(self, user_id: int, user: UserUpdate) -> Optional[UserSchema]:
        """Update a user."""
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
        """Delete a user."""
        db_user = self.get_user(user_id)
        if not db_user:
            return False

        self.db.delete(db_user)
        self.db.commit()
        return True

    def change_user_role(self, user_id: int, role_name: str):
        """Change a user's role by replacing their current roles with the new one."""
        db_user = self.get_user(user_id)
        if not db_user:
            return None
        new_role = self.db.query(Role).filter(Role.name == role_name).first()
        if not new_role:
            return None
        db_user.roles = [new_role]
        db_user.role_id = new_role.id
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def authenticate_user(self, email: str, password: str) -> Optional[UserSchema]:
        """Authenticate a user."""
        print(
            f"DEBUG: Authenticating user with email: {email} and password length: {len(password)}"
        )
        user = self.get_user_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
