from typing import List, Optional

from sqlalchemy.orm import Session

from ..models.expense import Expense
from ..schemas.expense import ExpenseCreate


class ExpenseService:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[Expense]:
        return self.db.query(Expense).order_by(Expense.date.desc()).all()

    def get_by_plantation(self, plantation_id: int) -> List[Expense]:
        return (
            self.db.query(Expense)
            .filter(Expense.plantation_id == plantation_id)
            .order_by(Expense.date.desc())
            .all()
        )

    def create(self, data: ExpenseCreate) -> Expense:
        obj = Expense(**data.model_dump())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj
