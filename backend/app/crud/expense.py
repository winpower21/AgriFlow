from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from ..models.expense import Expense
from ..schemas.expense import ExpenseCreate, ExpenseUpdate


class ExpenseService:
    def __init__(self, db: Session):
        self.db = db

    def _base_query(self):
        return self.db.query(Expense).options(joinedload(Expense.category))

    def get_all(
        self,
        search: Optional[str] = None,
        category_id: Optional[int] = None,
        plantation_id: Optional[int] = None,
        vehicle_id: Optional[int] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> List[Expense]:
        q = self._base_query()
        if search:
            q = q.filter(Expense.description.ilike(f"%{search}%"))
        if category_id:
            q = q.filter(Expense.category_id == category_id)
        if plantation_id:
            q = q.filter(Expense.plantation_id == plantation_id)
        if vehicle_id:
            q = q.filter(Expense.vehicle_id == vehicle_id)
        if from_date:
            q = q.filter(Expense.date >= from_date)
        if to_date:
            q = q.filter(Expense.date <= to_date)
        return q.order_by(Expense.date.desc()).all()

    def get_by_plantation(self, plantation_id: int) -> List[Expense]:
        return (
            self._base_query()
            .filter(Expense.plantation_id == plantation_id)
            .order_by(Expense.date.desc())
            .all()
        )

    def create(self, data: ExpenseCreate) -> Expense:
        obj = Expense(**data.model_dump())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return self._base_query().filter(Expense.id == obj.id).first()

    def update(self, expense_id: int, data: ExpenseUpdate) -> Optional[Expense]:
        obj = self.db.query(Expense).filter(Expense.id == expense_id).first()
        if not obj:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        self.db.commit()
        return self._base_query().filter(Expense.id == expense_id).first()

    def delete(self, expense_id: int) -> bool:
        obj = self.db.query(Expense).filter(Expense.id == expense_id).first()
        if not obj:
            return False
        self.db.delete(obj)
        self.db.commit()
        return True
