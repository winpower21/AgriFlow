"""
Settings / lookup-table management router.

Provides full CRUD for the four domain lookup tables used across the
application:

1. **Transformation Types** — processing stages a batch can go through
   (e.g. CLEAN, DRY, BAG).
2. **Wage Types** — payment models for personnel (e.g. hourly, daily,
   per-piece).
3. **Batch Stages** — the ordered lifecycle stages a batch passes through
   (HARVEST -> CLEAN -> DRY -> BAG -> GRADE -> PACK -> RETAIL).
4. **Expense Categories** — classification labels for plantation expenses.

Endpoints (per entity)
----------------------
GET    /settings/<entity>            — List all records.
POST   /settings/<entity>            — Create a new record (201).
PUT    /settings/<entity>/{id}       — Update an existing record.
DELETE /settings/<entity>/{id}       — Delete a record (204).

Where ``<entity>`` is one of ``transformation-types``, ``wage-types``,
``batch-stages``, or ``expense-categories``.

Authentication / authorisation
------------------------------
All endpoints require a valid JWT (``get_current_user`` at the router
level).  There is **no** additional admin-role restriction — any
authenticated user can manage these lookup tables.

Request / response schemas
--------------------------
Each entity has a triplet: ``*Create``, ``*Update``, ``*Schema``.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.dependencies import get_current_user
from ..crud.settings import SettingsService
from ..database import get_db
from ..schemas.settings import (
    AppConfigSchema,
    AppConfigUpdate,
    BatchStageCreate,
    BatchStageSchema,
    BatchStageUpdate,
    ExpenseCategoryCreate,
    ExpenseCategorySchema,
    ExpenseCategoryUpdate,
    WageTypeCreate,
    WageTypeSchema,
    WageTypeUpdate,
)
from ..schemas.transformation import (
    TransformationTypeCreate,
    TransformationTypeSchema,
    TransformationTypeUpdate,
)

# Auth: ``get_current_user`` at the router level — every endpoint requires a
# valid JWT bearer token.  No additional role-based restrictions are applied.
router = APIRouter(
    prefix="/settings",
    tags=["settings"],
    dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)


# ── Transformation Types ─────────────────────────────
# Define the processing stage types available for batch transformations
# (e.g. CLEAN, DRY, BAG, GRADE, PACK).


@router.get("/transformation-types", response_model=list[TransformationTypeSchema])
def get_transformation_types(db: Session = Depends(get_db)):
    """Retrieve all transformation types. Auth: any authenticated user."""
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
# Payment models for personnel (hourly, daily, per-piece, etc.).


@router.get("/wage-types", response_model=list[WageTypeSchema])
def get_wage_types(db: Session = Depends(get_db)):
    """Retrieve all wage types. Auth: any authenticated user."""
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
# Ordered lifecycle stages a batch moves through:
# HARVEST -> CLEAN -> DRY -> BAG -> GRADE -> PACK -> RETAIL


@router.get("/batch-stages", response_model=list[BatchStageSchema])
def get_batch_stages(db: Session = Depends(get_db)):
    """Retrieve all batch stages. Auth: any authenticated user."""
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
# Classification labels for plantation/operational expenses (e.g. transport,
# fertiliser, labour).


@router.get("/expense-categories", response_model=list[ExpenseCategorySchema])
def get_expense_categories(db: Session = Depends(get_db)):
    """Retrieve all expense categories. Auth: any authenticated user."""
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


# ── App Config ────────────────────────────────────────────────────────────────
# Runtime-configurable scalar settings (e.g. unit conversion rates).


@router.get("/app-config/{key}", response_model=AppConfigSchema)
def get_app_config(key: str, db: Session = Depends(get_db)):
    """Retrieve a single app config value by key. Returns 404 if not set. Auth: any user."""
    service = SettingsService(db)
    value = service.get_app_config(key)
    if value is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Config key '{key}' not found",
        )
    return {"key": key, "value": value}


@router.put("/app-config/{key}", response_model=AppConfigSchema)
def set_app_config(key: str, payload: AppConfigUpdate, db: Session = Depends(get_db)):
    """Create or update a single app config value. Auth: any user."""
    service = SettingsService(db)
    obj = service.set_app_config(key, payload.value)
    return obj
