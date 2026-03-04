from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user, roles_required
from app.models import User

router = APIRouter(tags=["general"])


@router.get("/home")
def home(user: User = Depends(get_current_user)):
    """
    Protected route: Accessible to any authenticated user.
    """
    return {
        "message": f"Welcome home, {user.email}!",
        "roles": [r.name for r in user.roles],
        "email": user.email,
    }


@router.get("/admin")
def admin_dashboard(user: User = Depends(roles_required("admin"))):
    """
    Protected route: Accessible only to users with 'admin' role.
    """
    return {
        "message": f"Welcome to the Admin Dashboard, {user.email}",
        "authorized": True,
    }
