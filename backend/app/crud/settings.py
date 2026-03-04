from typing import List, Optional

from sqlalchemy.orm import Session

from ..models.batch import BatchStage
from ..models.expense import ExpenseCategory
from ..models.personnel import WageType
from ..models.transformation import TransformationType
from ..schemas.settings import (
    BatchStageCreate,
    BatchStageUpdate,
    ExpenseCategoryCreate,
    ExpenseCategoryUpdate,
    TransformationTypeCreate,
    TransformationTypeUpdate,
    WageTypeCreate,
    WageTypeUpdate,
)


class SettingsService:
    def __init__(self, db: Session):
        self.db = db

    # ── Transformation Types ─────────────────────────

    def get_transformation_types(self) -> List[TransformationType]:
        """Retrieve all transformation types from the database."""
        return self.db.query(TransformationType).order_by(TransformationType.id).all()

    def get_transformation_type(self, type_id: int) -> Optional[TransformationType]:
        """Retrieve a specific transformation type by ID."""
        return self.db.query(TransformationType).filter(TransformationType.id == type_id).first()

    def create_transformation_type(self, data: TransformationTypeCreate) -> TransformationType:
        """Create a new transformation type in the database."""
        obj = TransformationType(**data.model_dump())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update_transformation_type(self, type_id: int, data: TransformationTypeUpdate) -> Optional[TransformationType]:
        """Update an existing transformation type in the database."""
        obj = self.get_transformation_type(type_id)
        if not obj:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete_transformation_type(self, type_id: int) -> bool:
        """Delete a transformation type from the database."""
        obj = self.get_transformation_type(type_id)
        if not obj:
            return False
        self.db.delete(obj)
        self.db.commit()
        return True

    # ── Wage Types ───────────────────────────────────

    def get_wage_types(self) -> List[WageType]:
        """Retrieve all wage types from the database."""
        return self.db.query(WageType).order_by(WageType.id).all()

    def get_wage_type(self, type_id: int) -> Optional[WageType]:
        """Retrieve a specific wage type by ID."""
        return self.db.query(WageType).filter(WageType.id == type_id).first()

    def create_wage_type(self, data: WageTypeCreate) -> WageType:
        """Create a new wage type in the database."""
        obj = WageType(**data.model_dump())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update_wage_type(self, type_id: int, data: WageTypeUpdate) -> Optional[WageType]:
        """Update an existing wage type in the database."""
        obj = self.get_wage_type(type_id)
        if not obj:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete_wage_type(self, type_id: int) -> bool:
        """Delete a wage type from the database."""
        obj = self.get_wage_type(type_id)
        if not obj:
            return False
        self.db.delete(obj)
        self.db.commit()
        return True

    # ── Batch Stages ─────────────────────────────────

    def get_batch_stages(self) -> List[BatchStage]:
        """Retrieve all batch stages from the database."""
        return self.db.query(BatchStage).order_by(BatchStage.id).all()

    def get_batch_stage(self, stage_id: int) -> Optional[BatchStage]:
        """Retrieve a specific batch stage by ID."""
        return self.db.query(BatchStage).filter(BatchStage.id == stage_id).first()

    def create_batch_stage(self, data: BatchStageCreate) -> BatchStage:
        """Create a new batch stage in the database."""
        obj = BatchStage(**data.model_dump())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update_batch_stage(self, stage_id: int, data: BatchStageUpdate) -> Optional[BatchStage]:
        """Update an existing batch stage in the database."""
        obj = self.get_batch_stage(stage_id)
        if not obj:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete_batch_stage(self, stage_id: int) -> bool:
        """Delete a batch stage from the database."""
        obj = self.get_batch_stage(stage_id)
        if not obj:
            return False
        self.db.delete(obj)
        self.db.commit()
        return True

    # ── Expense Categories ────────────────────────────

    def get_expense_categories(self) -> List[ExpenseCategory]:
        return self.db.query(ExpenseCategory).order_by(ExpenseCategory.id).all()

    def get_expense_category(self, cat_id: int) -> Optional[ExpenseCategory]:
        return (
            self.db.query(ExpenseCategory)
            .filter(ExpenseCategory.id == cat_id)
            .first()
        )

    def get_expense_category_by_name(self, name: str) -> Optional[ExpenseCategory]:
        return (
            self.db.query(ExpenseCategory)
            .filter(ExpenseCategory.name == name)
            .first()
        )

    def create_expense_category(self, data: ExpenseCategoryCreate) -> ExpenseCategory:
        obj = ExpenseCategory(**data.model_dump())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update_expense_category(
        self, cat_id: int, data: ExpenseCategoryUpdate
    ) -> Optional[ExpenseCategory]:
        obj = self.get_expense_category(cat_id)
        if not obj:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete_expense_category(self, cat_id: int) -> bool:
        obj = self.get_expense_category(cat_id)
        if not obj:
            return False
        self.db.delete(obj)
        self.db.commit()
        return True
