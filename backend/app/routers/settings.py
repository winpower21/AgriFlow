from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.dependencies import get_current_user
from ..crud.settings import SettingsService
from ..database import get_db
from ..schemas.settings import (
    BatchStageCreate,
    BatchStageSchema,
    BatchStageUpdate,
    ExpenseCategoryCreate,
    ExpenseCategorySchema,
    ExpenseCategoryUpdate,
    TransformationTypeCreate,
    TransformationTypeSchema,
    TransformationTypeUpdate,
    WageTypeCreate,
    WageTypeSchema,
    WageTypeUpdate,
)

router = APIRouter(
    prefix="/settings",
    tags=["settings"],
    dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)


# ── Transformation Types ─────────────────────────────


@router.get("/transformation-types", response_model=list[TransformationTypeSchema])
def get_transformation_types(db: Session = Depends(get_db)):
    """Retrieve all transformation types."""
    service = SettingsService(db)
    return service.get_transformation_types()


@router.post("/transformation-types", response_model=TransformationTypeSchema, status_code=201)
def create_transformation_type(data: TransformationTypeCreate, db: Session = Depends(get_db)):
    """Create a new transformation type."""
    service = SettingsService(db)
    return service.create_transformation_type(data)


@router.put("/transformation-types/{type_id}", response_model=TransformationTypeSchema)
def update_transformation_type(type_id: int, data: TransformationTypeUpdate, db: Session = Depends(get_db)):
    """Update an existing transformation type."""
    service = SettingsService(db)
    result = service.update_transformation_type(type_id, data)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transformation type not found")
    return result


@router.delete("/transformation-types/{type_id}", status_code=204)
def delete_transformation_type(type_id: int, db: Session = Depends(get_db)):
    """Delete a transformation type."""
    service = SettingsService(db)
    if not service.delete_transformation_type(type_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transformation type not found")


# ── Wage Types ───────────────────────────────────────


@router.get("/wage-types", response_model=list[WageTypeSchema])
def get_wage_types(db: Session = Depends(get_db)):
    """Retrieve all wage types."""
    service = SettingsService(db)
    return service.get_wage_types()


@router.post("/wage-types", response_model=WageTypeSchema, status_code=201)
def create_wage_type(data: WageTypeCreate, db: Session = Depends(get_db)):
    """Create a new wage type."""
    service = SettingsService(db)
    return service.create_wage_type(data)


@router.put("/wage-types/{type_id}", response_model=WageTypeSchema)
def update_wage_type(type_id: int, data: WageTypeUpdate, db: Session = Depends(get_db)):
    """Update an existing wage type."""
    service = SettingsService(db)
    result = service.update_wage_type(type_id, data)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wage type not found")
    return result


@router.delete("/wage-types/{type_id}", status_code=204)
def delete_wage_type(type_id: int, db: Session = Depends(get_db)):
    """Delete a wage type."""
    service = SettingsService(db)
    if not service.delete_wage_type(type_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wage type not found")


# ── Batch Stages ─────────────────────────────────────


@router.get("/batch-stages", response_model=list[BatchStageSchema])
def get_batch_stages(db: Session = Depends(get_db)):
    """Retrieve all batch stages."""
    service = SettingsService(db)
    return service.get_batch_stages()


@router.post("/batch-stages", response_model=BatchStageSchema, status_code=201)
def create_batch_stage(data: BatchStageCreate, db: Session = Depends(get_db)):
    """Create a new batch stage."""
    service = SettingsService(db)
    return service.create_batch_stage(data)


@router.put("/batch-stages/{stage_id}", response_model=BatchStageSchema)
def update_batch_stage(stage_id: int, data: BatchStageUpdate, db: Session = Depends(get_db)):
    """Update an existing batch stage."""
    service = SettingsService(db)
    result = service.update_batch_stage(stage_id, data)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch stage not found")
    return result


@router.delete("/batch-stages/{stage_id}", status_code=204)
def delete_batch_stage(stage_id: int, db: Session = Depends(get_db)):
    """Delete a batch stage."""
    service = SettingsService(db)
    if not service.delete_batch_stage(stage_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch stage not found")


# ── Expense Categories ──────────────────────────────


@router.get("/expense-categories", response_model=list[ExpenseCategorySchema])
def get_expense_categories(db: Session = Depends(get_db)):
    """Retrieve all expense categories."""
    service = SettingsService(db)
    return service.get_expense_categories()


@router.post("/expense-categories", response_model=ExpenseCategorySchema, status_code=201)
def create_expense_category(data: ExpenseCategoryCreate, db: Session = Depends(get_db)):
    """Create a new expense category."""
    service = SettingsService(db)
    return service.create_expense_category(data)


@router.put("/expense-categories/{cat_id}", response_model=ExpenseCategorySchema)
def update_expense_category(cat_id: int, data: ExpenseCategoryUpdate, db: Session = Depends(get_db)):
    """Update an existing expense category."""
    service = SettingsService(db)
    result = service.update_expense_category(cat_id, data)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense category not found")
    return result


@router.delete("/expense-categories/{cat_id}", status_code=204)
def delete_expense_category(cat_id: int, db: Session = Depends(get_db)):
    """Delete an expense category."""
    service = SettingsService(db)
    if not service.delete_expense_category(cat_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense category not found")
