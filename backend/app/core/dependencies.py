"""
FastAPI Dependencies — Authentication and Role-Based Access Control
====================================================================

This module supplies reusable ``Depends()`` callables for protecting routes:

- **``get_current_user``** — Extracts the Bearer token from the
  ``Authorization`` header (via OAuth2PasswordBearer), decodes the JWT,
  and returns the corresponding ``User`` ORM object.  Raises 401 if the
  token is missing, expired, or does not map to a valid user.

- **``roles_required(role)``** — Dependency *factory* that returns an
  inner checker.  The checker calls ``get_current_user`` first, then
  verifies the user possesses a specific role.  Raises 403 on mismatch.

- **``roles_accepted(roles)``** — Like ``roles_required`` but accepts a
  *list* of roles and succeeds if the user holds **any** one of them.

Typical usage in a router::

    @router.get("/admin-only")
    def admin_endpoint(user: User = Depends(roles_required("admin"))):
        ...

    @router.get("/staff")
    def staff_endpoint(user: User = Depends(roles_accepted(["admin", "manager"]))):
        ...
"""

from typing import Annotated, List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.crud import UserService

# from app.crud.user import get_user, get_user_roles   # Legacy import (now using UserService)
from app.database import get_db
from app.models import User

# ---------------------------------------------------------------------------
# OAuth2 token extraction scheme
# ---------------------------------------------------------------------------
# ``tokenUrl`` tells the Swagger UI where to POST credentials to obtain a
# token.  The actual login logic lives in the ``auth`` router at "auth/login".
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# ---------------------------------------------------------------------------
# Core authentication dependency
# ---------------------------------------------------------------------------
def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
) -> User:
    """
    Validate the JWT Bearer token and return the authenticated ``User``.

    Steps:
        1. Decode the token using the application secret and algorithm.
        2. Extract the ``"user"`` claim (contains the user's primary-key id,
           stored as an int but transported as a string in the JWT payload).
        3. Look up the user in the database via ``UserService.get_user``.
        4. Raise ``HTTP 401`` if any step fails.

    Returns:
        The ``User`` ORM instance for the authenticated caller.
    """
    # Pre-build the 401 response so it can be raised from multiple places
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        print(f"DEBUG get_current_user: token received = {token[:20]}...")
        # Decode and verify signature + expiration in one step
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        print(f"DEBUG get_current_user: payload = {payload}")

        # The ``"user"`` key holds the user's database ID (set during login
        # in ``create_access_token({"user": user.id})``).
        id: str = payload.get("user")
        if id is None:
            print("DEBUG get_current_user: FAIL - 'user' key not in payload")
            raise credentials_exception
    except JWTError as e:
        # Covers expired tokens, tampered signatures, malformed JWTs, etc.
        print(f"DEBUG get_current_user: FAIL - JWTError: {e}")
        raise credentials_exception

    # Fetch the full user record from the database
    user_service = UserService(db)
    user = user_service.get_user(user_id=int(id))
    if user is None:
        print(f"DEBUG get_current_user: FAIL - no user found for id={id}")
        raise credentials_exception
    print(f"DEBUG get_current_user: SUCCESS - user={user.email}")
    return user


# ---------------------------------------------------------------------------
# Role-based access control dependencies
# ---------------------------------------------------------------------------

def roles_required(required_role: str):
    """
    Dependency factory: enforce that the caller has *exactly* the given role.

    Args:
        required_role: The role name that the user must possess (e.g. ``"admin"``).

    Returns:
        A dependency callable suitable for ``Depends(roles_required("admin"))``.
        The inner function resolves the current user (triggering JWT validation),
        then checks their roles.  Returns the ``User`` on success or raises
        ``HTTP 403`` on failure.
    """

    def role_checker(
        user: User = Depends(get_current_user), db: Session = Depends(get_db)
    ) -> User:
        # Fetch the list of role names associated with this user
        user_service = UserService(db)
        user_roles = user_service.get_user_roles(user_or_id=user)

        if required_role not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User must have '{required_role}' role to access this resource",
            )

        return user

    return role_checker


def roles_accepted(accepted_roles: List[str]):
    """
    Dependency factory: enforce that the caller has *at least one* of the
    specified roles.

    This is more permissive than ``roles_required`` and is useful for
    endpoints shared between multiple privilege levels (e.g. both admins
    and managers).

    Args:
        accepted_roles: A list of role names, any one of which grants access.

    Returns:
        A dependency callable suitable for
        ``Depends(roles_accepted(["admin", "manager"]))``.
    """

    def role_checker(
        user: User = Depends(get_current_user), db: Session = Depends(get_db)
    ) -> User:
        # Fetch the list of role names associated with this user
        user_service = UserService(db)
        user_roles = user_service.get_user_roles(user_or_id=user)

        # Succeed if there is any overlap between the user's roles and the accepted set
        if not any(role in user_roles for role in accepted_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User must have one of these roles: {', '.join(accepted_roles)}",
            )

        return user

    return role_checker
