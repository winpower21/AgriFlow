from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..core.dependencies import get_current_user, roles_required
from ..crud.expense import ExpenseService
from ..crud.settings import SettingsService
from ..database import get_db
from ..schemas.expense import ExpenseCreate, ExpenseSchema, ExpenseUpdate
from ..schemas.response import ApiResponse

router = APIRouter(
    prefix="/expenses",
    tags=["expenses"],
    dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=ApiResponse[list[ExpenseSchema]])
def get_all_expenses(
    search: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    plantation_id: Optional[int] = Query(None),
    vehicle_id: Optional[int] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=ExpenseService(db).get_all(
        search=search,
        category_id=category_id,
        plantation_id=plantation_id,
        vehicle_id=vehicle_id,
        from_date=from_date,
        to_date=to_date,
    ))


@router.get("/by-plantation/{plantation_id}", response_model=ApiResponse[list[ExpenseSchema]])
def get_expenses_by_plantation(plantation_id: int, db: Session = Depends(get_db)):
    return ApiResponse(data=ExpenseService(db).get_by_plantation(plantation_id))


@router.post("/", response_model=ApiResponse[ExpenseSchema], status_code=201,
             dependencies=[Depends(roles_required("admin"))])
def create_expense(data: ExpenseCreate, db: Session = Depends(get_db)):
    settings_service = SettingsService(db)
    if not settings_service.get_expense_category(data.category_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense category not found")
    return ApiResponse(data=ExpenseService(db).create(data), message="Expense created successfully", type="success")


@router.put("/{expense_id}", response_model=ApiResponse[ExpenseSchema],
            dependencies=[Depends(roles_required("admin"))])
def update_expense(expense_id: int, data: ExpenseUpdate, db: Session = Depends(get_db)):
    result = ExpenseService(db).update(expense_id, data)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    return ApiResponse(data=result, message="Expense updated successfully", type="success")


@router.delete("/{expense_id}", response_model=ApiResponse[None],
               dependencies=[Depends(roles_required("admin"))])
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    result = ExpenseService(db).delete(expense_id)
    if result == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    if result == "linked_to_purchase":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This expense was auto-generated from a consumable purchase. Delete the purchase instead.",
        )
    return ApiResponse(data=None, message="Expense deleted successfully", type="success")
