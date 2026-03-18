from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from ..models.consumables import (
    Consumable,
    ConsumableCategory,
    ConsumableConsumption,
    ConsumablePurchase,
    ConsumptionAllocation,
)
from ..models.expense import Expense, ExpenseCategory
from ..schemas.consumable import (
    ConsumableCategoryCreate,
    ConsumableCreate,
    ConsumablePurchaseCreate,
    ConsumableUpdate,
)


class ConsumableService:
    def __init__(self, db: Session):
        self.db = db

    # ── Categories ────────────────────────────────────────────────────────────

    def get_all_categories(self) -> List[ConsumableCategory]:
        return self.db.query(ConsumableCategory).order_by(ConsumableCategory.name).all()

    def get_category_by_id(self, category_id: int) -> Optional[ConsumableCategory]:
        return (
            self.db.query(ConsumableCategory)
            .filter(ConsumableCategory.id == category_id)
            .first()
        )

    def create_category(self, data: ConsumableCategoryCreate) -> ConsumableCategory:
        obj = ConsumableCategory(**data.model_dump())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete_category(self, category_id: int) -> bool:
        obj = self.get_category_by_id(category_id)
        if not obj:
            return False
        self.db.delete(obj)
        self.db.commit()
        return True

    # ── Consumable items ──────────────────────────────────────────────────────

    def get_all(
        self, search: Optional[str] = None, category_id: Optional[int] = None
    ) -> List[Consumable]:
        q = self.db.query(Consumable)
        if search:
            q = q.filter(Consumable.name.ilike(f"%{search}%"))
        if category_id:
            q = q.filter(Consumable.category_id == category_id)
        return q.order_by(Consumable.name).all()

    def get_by_id(self, consumable_id: int) -> Optional[Consumable]:
        return self.db.query(Consumable).filter(Consumable.id == consumable_id).first()

    def create(self, data: ConsumableCreate) -> Consumable:
        obj = Consumable(**data.model_dump())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(
        self, consumable_id: int, data: ConsumableUpdate
    ) -> Optional[Consumable]:
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

    def get_all_purchases(
        self, consumable_id: Optional[int] = None
    ) -> List[ConsumablePurchase]:
        q = self.db.query(ConsumablePurchase)
        if consumable_id:
            q = q.filter(ConsumablePurchase.consumable_id == consumable_id)
        return q.order_by(ConsumablePurchase.purchase_date.desc()).all()

    def add_purchase(
        self, consumable_id: int, data: ConsumablePurchaseCreate
    ) -> Optional[ConsumablePurchase]:
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

    def delete_purchase(self, purchase_id: int) -> Optional[str]:
        """Delete a purchase lot.

        Returns:
            None on success.
            "not_found" if the purchase doesn't exist.
            "has_allocations" if the lot has been partially/fully consumed (FIFO locks it).
        """
        purchase = (
            self.db.query(ConsumablePurchase)
            .filter(ConsumablePurchase.id == purchase_id)
            .first()
        )
        if not purchase:
            return "not_found"
        has_alloc = (
            self.db.query(ConsumptionAllocation)
            .filter(ConsumptionAllocation.purchase_id == purchase_id)
            .first()
        )
        if has_alloc:
            return "has_allocations"
        # Delete the linked auto-generated expense if present
        if purchase.expense_id:
            expense = (
                self.db.query(Expense).filter(Expense.id == purchase.expense_id).first()
            )
            if expense:
                self.db.delete(expense)
        self.db.delete(purchase)
        self.db.commit()
        return None

    def record_consumption(
        self,
        consumable_id: int,
        quantity_used,
        transformation_id: int,
        consumption_date,
        notes: str = None,
    ) -> Optional[str]:
        """FIFO consumable allocation. Returns None on success or error string."""
        from decimal import Decimal as D

        consumable = self.get_by_id(consumable_id)
        if not consumable:
            return "consumable_not_found"

        # Validate total available stock
        lots_available = (
            self.db.query(ConsumablePurchase)
            .filter(
                ConsumablePurchase.consumable_id == consumable_id,
                ConsumablePurchase.remaining_quantity > 0,
            )
            .all()
        )
        total_available = sum((p.remaining_quantity for p in lots_available), D("0"))
        if total_available < D(str(quantity_used)):
            return "insufficient_stock"

        # Create consumption record
        consumption = ConsumableConsumption(
            transformation_id=transformation_id,
            consumable_id=consumable_id,
            consumption_date=consumption_date,
            quantity_used=quantity_used,
            total_cost=D("0"),
            notes=notes,
        )
        self.db.add(consumption)
        self.db.flush()

        # FIFO allocation across purchase lots ordered by purchase_date ASC
        lots = (
            self.db.query(ConsumablePurchase)
            .filter(
                ConsumablePurchase.consumable_id == consumable_id,
                ConsumablePurchase.remaining_quantity > 0,
            )
            .order_by(ConsumablePurchase.purchase_date.asc())
            .all()
        )

        remaining_to_allocate = D(str(quantity_used))
        total_cost = D("0")

        for lot in lots:
            if remaining_to_allocate <= 0:
                break
            allocate = min(lot.remaining_quantity, remaining_to_allocate)
            cost = allocate * lot.unit_cost
            alloc = ConsumptionAllocation(
                consumption_id=consumption.id,
                purchase_id=lot.id,
                quantity_allocated=allocate,
                cost=cost,
            )
            self.db.add(alloc)
            lot.remaining_quantity -= allocate
            remaining_to_allocate -= allocate
            total_cost += cost

        consumption.total_cost = total_cost
        self.db.commit()
        return None

    def delete_consumable(self, consumable_id: int) -> Optional[str]:
        """Delete a consumable item and cascade to its purchases + linked expenses.

        Returns:
            None on success.
            "not_found" if the consumable doesn't exist.
            "has_consumptions" if any consumption records exist (item has been used).
        """
        consumable = self.get_by_id(consumable_id)
        if not consumable:
            return "not_found"
        has_consumption = (
            self.db.query(ConsumableConsumption)
            .filter(ConsumableConsumption.consumable_id == consumable_id)
            .first()
        )
        if has_consumption:
            return "has_consumptions"
        # Cascade: delete each purchase and its linked expense
        for purchase in list(consumable.purchases):
            if purchase.expense_id:
                expense = (
                    self.db.query(Expense)
                    .filter(Expense.id == purchase.expense_id)
                    .first()
                )
                if expense:
                    self.db.delete(expense)
            self.db.delete(purchase)
        self.db.delete(consumable)
        self.db.commit()
        return None
