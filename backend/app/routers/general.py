"""
General / test-dashboard router.

Provides lightweight endpoints used to verify that authentication and
role-based access control are working correctly.  These are primarily
useful during development and for health-check/smoke-test purposes.

Endpoints
---------
GET /home   — Returns a welcome message with the caller's email and roles.
              **Auth:** any authenticated user (``get_current_user``).
GET /admin  — Returns a simple admin-dashboard payload.
              **Auth:** admin role required (``roles_required("admin")``).

NOTE: Neither endpoint has a ``/prefix`` — they are mounted at the
application root (e.g. ``http://localhost:8000/home``).
"""

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user, roles_required
from app.models import User
from app.schemas.response import ApiResponse

# No prefix — endpoints are available at the application root.
router = APIRouter(tags=["general"])


# Auth: injects the current user via ``get_current_user`` dependency —
# any valid JWT holder can access this endpoint.
@router.get("/home", response_model=ApiResponse[dict])
def home(user: User = Depends(get_current_user)):
    """
    Protected route: Accessible to any authenticated user.

    Returns basic user information (email, roles) to confirm the token
    is valid and to identify the caller.
    """
    return ApiResponse(data={
        "message": f"Welcome home, {user.email}!",
        "roles": [r.name for r in user.roles],
        "email": user.email,
    })


# Auth: ``roles_required("admin")`` both authenticates and checks the admin
# role in a single dependency — returns 403 if the user lacks the role.
@router.get("/admin", response_model=ApiResponse[dict])
def admin_dashboard(user: User = Depends(roles_required("admin"))):
    """
    Protected route: Accessible only to users with the ``admin`` role.

    Returns a confirmation message.  Useful for verifying admin access.
    """
    return ApiResponse(data={
        "message": f"Welcome to the Admin Dashboard, {user.email}",
        "authorized": True,
    })
