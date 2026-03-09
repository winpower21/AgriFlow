"""
Settings CRUD service module.

Provides ``SettingsService``, a single service class that manages all
application-level configuration / lookup-table entities used throughout
AgriFlow:

  - **TransformationType** — defines the kinds of processing steps
    (e.g., CLEAN, DRY, BAG, GRADE) that can be applied to batches.
  - **WageType** — categorises how personnel are compensated (hourly,
    daily, per-piece, etc.).
  - **BatchStage** — enumerates the lifecycle stages a batch can pass
    through (HARVEST -> CLEAN -> DRY -> BAG -> GRADE -> PACK -> RETAIL).
  - **ExpenseCategory** — classifies expenses (fertiliser, transport,
    equipment rental, etc.).

All four entity groups follow an identical CRUD pattern:
  1. **List** — returns all rows ordered by ``id``.
  2. **Get by ID** — single-row lookup by primary key.
  3. **Create** — inserts a new row from a validated Pydantic schema.
  4. **Update** — partial update (``exclude_unset=True``) of an
     existing row; returns None if the row does not exist.
  5. **Delete** — removes a row by ID; returns bool success indicator.

ExpenseCategory additionally offers a ``get_expense_category_by_name()``
lookup for uniqueness checks before creating duplicates.

Design rationale: Grouping these lightweight entities into one service
keeps the settings/admin API surface consolidated and avoids a
proliferation of tiny service classes.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from ..models.batch import BatchStage
from ..models.expense import ExpenseCategory
from ..models.personnel import WageType
from ..models.settings import AppConfig
from ..models.transformation import TransformationType
from ..schemas.settings import (
    BatchStageCreate,
    BatchStageUpdate,
    ExpenseCategoryCreate,
    ExpenseCategoryUpdate,
    WageTypeCreate,
    WageTypeUpdate,
)
from ..schemas.transformation import (
    TransformationTypeCreate,
    TransformationTypeUpdate,
)


class SettingsService:
    """Unified service class for application configuration entities.

    Manages TransformationType, WageType, BatchStage, and ExpenseCategory
    records.  Follows the service-object pattern: instantiate with a
    SQLAlchemy ``Session``, then call the appropriate CRUD method.

    Attributes:
        db: The active SQLAlchemy session used for all queries.
    """

    def __init__(self, db: Session):
        self.db = db

    # ── Transformation Types ─────────────────────────
    # Define the kinds of processing steps that can be applied to batches.
    # These are referenced by Transformation records to categorise what
    # operation was performed (e.g., cleaning, drying, grading).

    def get_transformation_types(self) -> List[TransformationType]:
        """Retrieve all transformation types, ordered by ID."""
        return self.db.query(TransformationType).order_by(TransformationType.id).all()

    def get_transformation_type(self, type_id: int) -> Optional[TransformationType]:
        """Retrieve a specific transformation type by primary key."""
        return self.db.query(TransformationType).filter(TransformationType.id == type_id).first()

    def create_transformation_type(self, data: TransformationTypeCreate) -> TransformationType:
        """Create a new transformation type from the validated schema."""
        obj = TransformationType(**data.model_dump())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update_transformation_type(self, type_id: int, data: TransformationTypeUpdate) -> Optional[TransformationType]:
        """Partially update an existing transformation type.

        Only fields explicitly provided in the payload are modified
        (``exclude_unset=True``).  Returns None if the type ID is not found.
        """
        obj = self.get_transformation_type(type_id)
        if not obj:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete_transformation_type(self, type_id: int) -> bool:
        """Delete a transformation type by ID.  Returns False if not found."""
        obj = self.get_transformation_type(type_id)
        if not obj:
            return False
        self.db.delete(obj)
        self.db.commit()
        return True

    # ── Wage Types ───────────────────────────────────
    # Categorise how personnel are compensated.  Referenced by Personnel
    # records (via FK) and frozen onto TransformationPersonnel rows at
    # event time for historical cost accuracy.

    def get_wage_types(self) -> List[WageType]:
        """Retrieve all wage types, ordered by ID."""
        return self.db.query(WageType).order_by(WageType.id).all()

    def get_wage_type(self, type_id: int) -> Optional[WageType]:
        """Retrieve a specific wage type by primary key."""
        return self.db.query(WageType).filter(WageType.id == type_id).first()

    def create_wage_type(self, data: WageTypeCreate) -> WageType:
        """Create a new wage type from the validated schema."""
        obj = WageType(**data.model_dump())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update_wage_type(self, type_id: int, data: WageTypeUpdate) -> Optional[WageType]:
        """Partially update an existing wage type.

        Only fields explicitly provided in the payload are modified.
        Returns None if the wage type ID is not found.
        """
        obj = self.get_wage_type(type_id)
        if not obj:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete_wage_type(self, type_id: int) -> bool:
        """Delete a wage type by ID.  Returns False if not found."""
        obj = self.get_wage_type(type_id)
        if not obj:
            return False
        self.db.delete(obj)
        self.db.commit()
        return True

    # ── Batch Stages ─────────────────────────────────
    # Enumerate the lifecycle stages a batch passes through.  The
    # standard pipeline is HARVEST -> CLEAN -> DRY -> BAG -> GRADE ->
    # PACK -> RETAIL, but stages are configurable via this table.

    def get_batch_stages(self) -> List[BatchStage]:
        """Retrieve all batch stages, ordered by ID."""
        return self.db.query(BatchStage).order_by(BatchStage.id).all()

    def get_batch_stage(self, stage_id: int) -> Optional[BatchStage]:
        """Retrieve a specific batch stage by primary key."""
        return self.db.query(BatchStage).filter(BatchStage.id == stage_id).first()

    def create_batch_stage(self, data: BatchStageCreate) -> BatchStage:
        """Create a new batch stage from the validated schema."""
        obj = BatchStage(**data.model_dump())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update_batch_stage(self, stage_id: int, data: BatchStageUpdate) -> Optional[BatchStage]:
        """Partially update an existing batch stage.

        Only fields explicitly provided in the payload are modified.
        Returns None if the batch stage ID is not found.
        """
        obj = self.get_batch_stage(stage_id)
        if not obj:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete_batch_stage(self, stage_id: int) -> bool:
        """Delete a batch stage by ID.  Returns False if not found."""
        obj = self.get_batch_stage(stage_id)
        if not obj:
            return False
        self.db.delete(obj)
        self.db.commit()
        return True

    # ── Expense Categories ────────────────────────────
    # Classify expenses into buckets (e.g., fertiliser, transport,
    # equipment rental).  Referenced by Expense records via FK.

    def get_expense_categories(self) -> List[ExpenseCategory]:
        """Retrieve all expense categories, ordered by ID."""
        return self.db.query(ExpenseCategory).order_by(ExpenseCategory.id).all()

    def get_expense_category(self, cat_id: int) -> Optional[ExpenseCategory]:
        """Retrieve a specific expense category by primary key."""
        return (
            self.db.query(ExpenseCategory)
            .filter(ExpenseCategory.id == cat_id)
            .first()
        )

    def get_expense_category_by_name(self, name: str) -> Optional[ExpenseCategory]:
        """Look up an expense category by its unique name.

        Useful for checking duplicates before creating a new category
        or for matching imported data by name rather than ID.
        """
        return (
            self.db.query(ExpenseCategory)
            .filter(ExpenseCategory.name == name)
            .first()
        )

    def create_expense_category(self, data: ExpenseCategoryCreate) -> ExpenseCategory:
        """Create a new expense category from the validated schema."""
        obj = ExpenseCategory(**data.model_dump())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update_expense_category(
        self, cat_id: int, data: ExpenseCategoryUpdate
    ) -> Optional[ExpenseCategory]:
        """Partially update an existing expense category.

        Only fields explicitly provided in the payload are modified.
        Returns None if the category ID is not found.
        """
        obj = self.get_expense_category(cat_id)
        if not obj:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete_expense_category(self, cat_id: int) -> bool:
        """Delete an expense category by ID.  Returns False if not found."""
        obj = self.get_expense_category(cat_id)
        if not obj:
            return False
        self.db.delete(obj)
        self.db.commit()
        return True

    # ── App Config ────────────────────────────────────────────────────────────
    # Single-key/value settings for runtime-configurable scalar values
    # (e.g. unit conversion rates).

    def get_app_config(self, key: str, default: str = None) -> Optional[str]:
        """Return the string value for a config key, or ``default`` if not set."""
        obj = self.db.query(AppConfig).filter(AppConfig.key == key).first()
        return obj.value if obj else default

    def set_app_config(self, key: str, value: str) -> AppConfig:
        """Upsert a config key/value pair.

        Updates the existing row if the key exists, otherwise inserts a new one.
        """
        obj = self.db.query(AppConfig).filter(AppConfig.key == key).first()
        if obj:
            obj.value = value
        else:
            obj = AppConfig(key=key, value=value)
            self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj
