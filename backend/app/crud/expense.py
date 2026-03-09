"""
Expense CRUD service module.

Provides ``ExpenseService``, which manages expense records tied to
plantations.

Expenses are generic cost entries (e.g., fertiliser, transport, labour
hire) categorised via an ``ExpenseCategory`` FK.  Each expense is
associated with a specific plantation, allowing per-plantation cost
reporting and budgeting.

Key design notes:
  - **Reverse-chronological ordering**: Both ``get_all()`` and
    ``get_by_plantation()`` return results ordered by ``date DESC``
    so the most recent expenses appear first in listings.
  - **Minimal service**: Only list and create operations are exposed.
    Update and delete are not yet implemented.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from ..models.expense import Expense
from ..schemas.expense import ExpenseCreate


class ExpenseService:
    """Service class for expense-related database operations.

    Follows the service-object pattern: instantiate with a SQLAlchemy
    ``Session``, then call methods to query or create expense records.

    Attributes:
        db: The active SQLAlchemy session used for all queries.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[Expense]:
        """Return all expense records, newest first (by date descending)."""
        return self.db.query(Expense).order_by(Expense.date.desc()).all()

    def get_by_plantation(self, plantation_id: int) -> List[Expense]:
        """Return expenses for a specific plantation, newest first.

        Filters on the ``plantation_id`` FK so the caller receives only
        costs associated with a single plantation.
        """
        return (
            self.db.query(Expense)
            .filter(Expense.plantation_id == plantation_id)
            .order_by(Expense.date.desc())
            .all()
        )

    def create(self, data: ExpenseCreate) -> Expense:
        """Create a new expense record from the validated schema.

        The ``ExpenseCreate`` Pydantic model is dumped to a dict and
        unpacked into the Expense ORM constructor.  The record is
        committed immediately and the refreshed object (with
        server-generated defaults like ``id`` and timestamps) is
        returned.
        """
        obj = Expense(**data.model_dump())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj
