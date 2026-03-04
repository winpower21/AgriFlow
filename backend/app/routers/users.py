from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.dependencies import roles_required
from ..crud import UserService
from ..database import get_db
from ..schemas import RoleChange, User, UserCreate, UserUpdate

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/all",
    response_model=list[User],
    status_code=200,
    dependencies=[Depends(roles_required("admin"))],
)
def get_all_users(db: Session = Depends(get_db)):
    """
    Get a list of all users.
    """
    user_service = UserService(db)
    users = user_service.get_users()
    if users:
        return users
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No users found")


@router.post("/register", response_model=User, status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user.
    - **email**: Valid email address
    - **password**: User password (will be hashed)
    - **full_name**: Full name
    """
    user_service = UserService(db)
    # Check if user with email already exists
    db_user = user_service.get_user_by_email(email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )
    user_count = user_service.get_user_count()
    if user_count == 0:
        return user_service.create_admin_user(user=user)
    return user_service.create_user(user=user)


@router.get(
    "/unverified",
    response_model=list[User],
    status_code=200,
    dependencies=[Depends(roles_required("admin"))],
)
def get_unverified_users(db: Session = Depends(get_db)):
    """
    Get a list of unverified users.
    """
    user_service = UserService(db)
    unverified_users = user_service.get_unverified_users()
    if unverified_users:
        return unverified_users
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="No unverified users found"
    )


@router.delete(
    "/delete-user/{id}",
    response_model=User,
    status_code=200,
    dependencies=[Depends(roles_required("admin"))],
)
def delete_user(id: int, db: Session = Depends(get_db)):
    """
    Delete a user.
    """
    user_service = UserService(db)
    user = user_service.delete_user(user_id=id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return user


@router.put(
    "/update/{id}",
    response_model=User,
    status_code=200,
    dependencies=[Depends(roles_required("admin"))],
)
def update_user(id: int, user: UserUpdate, db: Session = Depends(get_db)):
    """
    Update a user.
    """
    user_service = UserService(db)
    user = user_service.update_user(user_id=id, user=user)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return user


@router.put(
    "/change-role/{id}",
    response_model=User,
    status_code=200,
    dependencies=[Depends(roles_required("admin"))],
)
def change_user_role(id: int, role_update: RoleChange, db: Session = Depends(get_db)):
    """
    Change a user's role. Replaces all existing roles with the specified one.
    """
    user_service = UserService(db)
    user = user_service.change_user_role(user_id=id, role_name=role_update.role)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User or role not found",
        )

    return user
