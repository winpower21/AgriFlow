"""
Router registry for the AgriFlow backend application.

This module centralises all API router imports and re-exports them via
``__all__`` so that ``app/main.py`` can mount every router with a single
star-import or explicit import list.

Registered routers
------------------
- **auth_router**        — Authentication (login / token issuance)
- **users_router**       — User management (registration, admin CRUD)
- **general_router**     — Simple test / dashboard endpoints
- **personnel_router**   — Personnel CRUD
- **plantation_router**  — Plantation CRUD with lease history
- **settings_router**    — Lookup-table management (transformation types,
                           wage types, batch stages, expense categories)
- **expense_router**     — Expense listing and creation
"""

from .auth import router as auth_router
from .expense import router as expense_router
from .general import router as general_router
from .personnel import router as personnel_router
from .plantation import router as plantation_router
from .settings import router as settings_router
from .users import router as users_router

__all__ = ["users_router", "auth_router", "general_router", "personnel_router", "plantation_router", "settings_router", "expense_router"]
