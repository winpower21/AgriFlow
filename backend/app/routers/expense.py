"""
Expense management router.

Provides endpoints for listing and creating expense records.  Expenses
are categorised via ``ExpenseCategory`` (managed in the settings router)
and optionally linked to a specific plantation.

Endpoints
---------
GET  /expenses/                              — List all expenses.             [all auth users]
GET  /expenses/by-plantation/{plantation_id} — Expenses for one plantation.   [all auth users]
POST /expenses/                              — Create a new expense.          [admin only]

Authentication / authorisation
------------------------------
- Router-level dependency: ``get_current_user`` (any valid JWT).
- The POST (create) endpoint additionally requires the ``admin`` role.

Validation
----------
Before creating an expense the endpoint validates that the referenced
``category_id`` exists in the database (via ``SettingsService``).  If not,
a 404 is returned.

Request / response schemas
--------------------------
- ``ExpenseCreate`` — body for POST (amount, date, category_id,
                      plantation_id, description, etc.)
- ``ExpenseSchema`` — response model with nested category info
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.dependencies import get_current_user, roles_required
from ..crud.expense import ExpenseService
from ..crud.settings import SettingsService
from ..database import get_db
from ..schemas.expense import ExpenseCreate, ExpenseSchema

# Auth: ``get_current_user`` at the router level — all endpoints need a valid
# JWT.  The create endpoint adds ``roles_required("admin")`` separately.
router = APIRouter(
    prefix="/expenses",
    tags=["expenses"],
    dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[ExpenseSchema])
def get_all_expenses(db: Session = Depends(get_db)):
    """Get all expenses. Available to all authenticated users."""
    service = ExpenseService(db)
    return service.get_all()


@router.get("/by-plantation/{plantation_id}", response_model=list[ExpenseSchema])
def get_expenses_by_plantation(plantation_id: int, db: Session = Depends(get_db)):
    """Get expenses filtered by plantation ID. Auth: any authenticated user."""
    service = ExpenseService(db)
    return service.get_by_plantation(plantation_id)


# ---------- Admin-only: create an expense ----------
@router.post(
    "/",
    response_model=ExpenseSchema,
    status_code=201,
    dependencies=[Depends(roles_required("admin"))],  # Auth: admin role required
)
def create_expense(data: ExpenseCreate, db: Session = Depends(get_db)):
    """Create a new expense record. **Auth:** admin only.

    Validates that ``category_id`` references an existing expense category
    before persisting.  Returns 404 if the category does not exist, or
    201 with the created record on success."""
    # Validate that the referenced expense category exists before creating
    settings_service = SettingsService(db)
    category = settings_service.get_expense_category(data.category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense category not found",
        )
    service = ExpenseService(db)
    return service.create(data)
