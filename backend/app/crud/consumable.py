from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from ..models.consumables import Consumable, ConsumablePurchase
from ..models.expense import Expense, ExpenseCategory
from ..schemas.consumable import ConsumableCreate, ConsumablePurchaseCreate, ConsumableUpdate


class ConsumableService:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, search: Optional[str] = None) -> List[Consumable]:
        q = self.db.query(Consumable)
        if search:
            q = q.filter(Consumable.name.ilike(f"%{search}%"))
        return q.order_by(Consumable.name).all()

    def get_by_id(self, consumable_id: int) -> Optional[Consumable]:
        return self.db.query(Consumable).filter(Consumable.id == consumable_id).first()

    def create(self, data: ConsumableCreate) -> Consumable:
        obj = Consumable(**data.model_dump())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, consumable_id: int, data: ConsumableUpdate) -> Optional[Consumable]:
        obj = self.get_by_id(consumable_id)
        if not obj:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get_purchases(self, consumable_id: int) -> List[ConsumablePurchase]:
        return (
            self.db.query(ConsumablePurchase)
            .filter(ConsumablePurchase.consumable_id == consumable_id)
            .order_by(ConsumablePurchase.purchase_date.desc())
            .all()
        )

    def get_all_purchases(self, consumable_id: Optional[int] = None) -> List[ConsumablePurchase]:
        q = self.db.query(ConsumablePurchase)
        if consumable_id:
            q = q.filter(ConsumablePurchase.consumable_id == consumable_id)
        return q.order_by(ConsumablePurchase.purchase_date.desc()).all()

    def add_purchase(self, consumable_id: int, data: ConsumablePurchaseCreate) -> Optional[ConsumablePurchase]:
        consumable = self.get_by_id(consumable_id)
        if not consumable:
            return None

        # Get or create the "Consumables" expense category
        category = (
            self.db.query(ExpenseCategory)
            .filter(ExpenseCategory.name.ilike("Consumables"))
            .first()
        )
        if not category:
            category = ExpenseCategory(
                name="Consumables",
                description="Expenses from consumable item purchases",
            )
            self.db.add(category)
            self.db.flush()

        # Auto-create a corresponding expense entry
        total_amount = data.quantity * data.unit_cost
        description = (
            f"Consumable purchase: {consumable.name} — "
            f"{data.quantity} {consumable.unit} @ ₹{data.unit_cost}/{consumable.unit}"
        )
        expense = Expense(
            date=data.purchase_date,
            amount=total_amount,
            category_id=category.id,
            description=description,
        )
        self.db.add(expense)
        self.db.flush()  # populate expense.id before linking

        purchase_data = data.model_dump()
        purchase_data["consumable_id"] = consumable_id
        purchase_data["remaining_quantity"] = data.quantity  # starts fully available
        purchase_data["expense_id"] = expense.id
        obj = ConsumablePurchase(**purchase_data)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get_stock_totals(self, consumable_id: int) -> dict:
        purchases = self.get_purchases(consumable_id)
        total_purchased = sum((p.quantity for p in purchases), Decimal("0"))
        total_remaining = sum((p.remaining_quantity for p in purchases), Decimal("0"))
        return {"total_purchased": total_purchased, "total_remaining": total_remaining}
