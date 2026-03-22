"""
User management router.

Endpoints
---------
POST   /users/register              — Public registration (no auth required).
                                      The very first user registered is
                                      automatically promoted to **admin**.
GET    /users/all                    — List all users.            [admin only]
GET    /users/unverified             — List unverified users.     [admin only]
DELETE /users/delete-user/{id}       — Delete a user by ID.       [admin only]
PUT    /users/update/{id}            — Update user details.       [admin only]
PUT    /users/change-role/{id}       — Replace a user's roles.    [admin only]

Authentication / authorisation
------------------------------
- ``/register`` is **unauthenticated** so new users can sign up.
- Every other endpoint requires the ``admin`` role, enforced via the
  ``roles_required("admin")`` dependency.

Request / response schemas
--------------------------
- ``UserCreate``  — registration payload (email, password, full_name)
- ``UserUpdate``  — partial update payload
- ``RoleChange``  — single-field body ``{ "role": "<role_name>" }``
- ``User``        — standard user response model
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.dependencies import roles_required
from ..crud import UserService
from ..database import get_db
from ..schemas import RoleChange, User, UserCreate, UserUpdate
from ..schemas.response import ApiResponse

# NOTE: No router-level auth dependency — individual endpoints opt in via
# ``dependencies=[Depends(roles_required("admin"))]``.  The /register
# endpoint deliberately remains public.
router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


# ---------- Admin-only: list all users ----------
@router.get(
    "/all",
    response_model=ApiResponse[list[User]],
    status_code=200,
    dependencies=[Depends(roles_required("admin"))],  # Auth: admin role required
)
def get_all_users(db: Session = Depends(get_db)):
    """
    Get a list of all users.

    **Auth:** admin only (via ``roles_required("admin")`` dependency).
    Returns 404 if no users exist in the database.
    """
    user_service = UserService(db)
    users = user_service.get_users()
    if users:
        return ApiResponse(data=users)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No users found")


# ---------- Public: user registration ----------
@router.post("/register", response_model=User, status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user (public — no authentication required).

    - **email**: Valid email address
    - **password**: User password (will be hashed)
    - **full_name**: Full name

    **First-user auto-admin:** When the database has zero users the first
    registrant is automatically assigned the ``admin`` role via
    ``create_admin_user()``.  Subsequent registrations create a regular
    (non-admin) user.

    Returns 400 if the email is already taken.
    """
    user_service = UserService(db)
    # Check if user with email already exists
    db_user = user_service.get_user_by_email(email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )
    # First-user auto-admin logic
    user_count = user_service.get_user_count()
    if user_count == 0:
        return user_service.create_admin_user(user=user)
    return user_service.create_user(user=user)


# ---------- Admin-only: list unverified users ----------
@router.get(
    "/unverified",
    response_model=ApiResponse[list[User]],
    status_code=200,
    dependencies=[Depends(roles_required("admin"))],  # Auth: admin role required
)
def get_unverified_users(db: Session = Depends(get_db)):
    """
    Get a list of unverified users.

    **Auth:** admin only.
    Returns 404 when there are no unverified users.
    """
    user_service = UserService(db)
    unverified_users = user_service.get_unverified_users()
    if unverified_users:
        return ApiResponse(data=unverified_users)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="No unverified users found"
    )


# ---------- Admin-only: delete a user ----------
@router.delete(
    "/delete-user/{id}",
    response_model=ApiResponse[User],
    status_code=200,
    dependencies=[Depends(roles_required("admin"))],  # Auth: admin role required
)
def delete_user(id: int, db: Session = Depends(get_db)):
    """
    Delete a user by ID.

    **Auth:** admin only.
    Returns 404 if the user does not exist.
    """
    user_service = UserService(db)
    user = user_service.delete_user(user_id=id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return ApiResponse(data=user, message="User deleted successfully", type="success")


# ---------- Admin-only: update a user ----------
@router.put(
    "/update/{id}",
    response_model=ApiResponse[User],
    status_code=200,
    dependencies=[Depends(roles_required("admin"))],  # Auth: admin role required
)
def update_user(id: int, user: UserUpdate, db: Session = Depends(get_db)):
    """
    Update a user's details.

    **Auth:** admin only.
    Accepts a partial ``UserUpdate`` body — only supplied fields are changed.
    Returns 404 if the user does not exist.
    """
    user_service = UserService(db)
    user = user_service.update_user(user_id=id, user=user)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return ApiResponse(data=user, message="User updated successfully", type="success")


# ---------- Admin-only: change a user's role ----------
@router.put(
    "/change-role/{id}",
    response_model=ApiResponse[User],
    status_code=200,
    dependencies=[Depends(roles_required("admin"))],  # Auth: admin role required
)
def change_user_role(id: int, role_update: RoleChange, db: Session = Depends(get_db)):
    """
    Change a user's role. Replaces **all** existing roles with the single
    role specified in the ``RoleChange`` body.

    **Auth:** admin only.
    Returns 404 if the user or the target role does not exist.
    """
    user_service = UserService(db)
    user = user_service.change_user_role(user_id=id, role_name=role_update.role)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User or role not found",
        )

    return ApiResponse(data=user, message="User role updated successfully", type="success")
