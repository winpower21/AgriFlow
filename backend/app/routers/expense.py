from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.dependencies import get_current_user, roles_required
from ..crud.expense import ExpenseService
from ..crud.settings import SettingsService
from ..database import get_db
from ..schemas.expense import ExpenseCreate, ExpenseSchema

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
    """Get expenses for a specific plantation."""
    service = ExpenseService(db)
    return service.get_by_plantation(plantation_id)


@router.post(
    "/",
    response_model=ExpenseSchema,
    status_code=201,
    dependencies=[Depends(roles_required("admin"))],
)
def create_expense(data: ExpenseCreate, db: Session = Depends(get_db)):
    """Create a new expense. Admin only."""
    # Validate category exists
    settings_service = SettingsService(db)
    category = settings_service.get_expense_category(data.category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense category not found",
        )
    service = ExpenseService(db)
    return service.create(data)
