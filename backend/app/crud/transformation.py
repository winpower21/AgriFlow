from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from ..models.batch import Batch
from ..models.consumables import ConsumableConsumption
from ..models.expense import Expense
from ..models.personnel import Personnel, TransformationPersonnel
from ..models.transformation import (
    Transformation,
    TransformationInput,
    TransformationOutput,
    TransformationType,
)
from ..models.vehicle import TransformationVehicle, Vehicle
from ..schemas.transformation import (
    TransformationConsumableCreate,
    TransformationCreate,
    TransformationExpenseCreate,
    TransformationOutputCreate,
    TransformationPersonnelCreate,
    TransformationPersonnelUpdate,
    TransformationUpdate,
    TransformationVehicleCreate,
    TransformationVehicleUpdate,
)


class TransformationService:
    def __init__(self, db: Session):
        self.db = db

    def _load_full(self, t_id: int) -> Optional[Transformation]:
        return (
            self.db.query(Transformation)
            .options(
                joinedload(Transformation.transformation_type),
                joinedload(Transformation.inputs).joinedload(TransformationInput.batch).joinedload(Batch.stage),
                joinedload(Transformation.outputs).joinedload(TransformationOutput.batch).joinedload(Batch.stage),
                joinedload(Transformation.personnel_assignments).joinedload(TransformationPersonnel.personnel),
                joinedload(Transformation.personnel_assignments).joinedload(TransformationPersonnel.wage_type),
                joinedload(Transformation.vehicle_usage).joinedload(TransformationVehicle.vehicle).joinedload(Vehicle.fuel_consumable),
                joinedload(Transformation.consumable_consumptions).joinedload(ConsumableConsumption.consumable),
                joinedload(Transformation.expenses).joinedload(Expense.category),
            )
            .filter(Transformation.id == t_id)
            .first()
        )

    def get_types(self) -> List[TransformationType]:
        return self.db.query(TransformationType).order_by(TransformationType.name).all()

    def get_all(
        self,
        type_id: Optional[int] = None,
        status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> List[Transformation]:
        q = (
            self.db.query(Transformation)
            .options(
                joinedload(Transformation.transformation_type),
                joinedload(Transformation.inputs).joinedload(TransformationInput.batch),
            )
        )
        if type_id:
            q = q.filter(Transformation.type_id == type_id)
        if status == "in_progress":
            q = q.filter(Transformation.to_date.is_(None))
        elif status == "complete":
            q = q.filter(Transformation.to_date.isnot(None))
        if date_from:
            q = q.filter(Transformation.from_date >= date_from)
        if date_to:
            q = q.filter(Transformation.from_date <= date_to)
        return q.order_by(Transformation.from_date.desc()).all()

    def get_by_id(self, t_id: int) -> Optional[Transformation]:
        return self._load_full(t_id)

    def create(self, data: TransformationCreate) -> Transformation:
        obj = Transformation(
            type_id=data.type_id,
            from_date=data.from_date,
            to_date=None,
            notes=data.notes,
        )
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return self._load_full(obj.id)

    def update(self, t_id: int, data: TransformationUpdate) -> Optional[str]:
        obj = self.db.query(Transformation).filter(Transformation.id == t_id).first()
        if not obj:
            return "not_found"
        if obj.to_date is not None:
            return "complete"
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        self.db.commit()
        return None

    def complete(self, t_id: int, completion_date: Optional[datetime] = None) -> Optional[str]:
        """Returns None on success, or error string."""
        obj = self.db.query(Transformation).filter(Transformation.id == t_id).first()
        if not obj:
            return "not_found"
        outputs = self.db.query(TransformationOutput).options(
            joinedload(TransformationOutput.batch).joinedload(Batch.stage)
        ).filter(
            TransformationOutput.transformation_id == t_id
        ).all()
        if not outputs:
            return "no_outputs"

        # Load transformation type for root/non-root checks
        transformation_type = self.db.query(TransformationType).filter(
            TransformationType.id == obj.type_id
        ).first()

        # Query inputs once — used for input gate, mass-balance, and cost calculation
        inputs = self.db.query(TransformationInput).filter(
            TransformationInput.transformation_id == t_id
        ).all()

        # Input gate: non-root transformations require at least one input
        if transformation_type and not transformation_type.is_root:
            if not inputs:
                return "non_root_no_inputs"

        # Mass-balance check: total input must equal total output (±0.01 kg tolerance)
        if transformation_type and not transformation_type.is_root:
            total_input = sum(Decimal(str(inp.input_weight)) for inp in inputs)
            total_output_weight = sum(o.output_weight for o in outputs)
            if abs(total_output_weight - total_input) > Decimal("0.01"):
                return "weight_mismatch"

        # Validate personnel assignments: sum of output_weight_considered <= total output weight
        total_output = sum(o.output_weight for o in outputs)
        personnel = self.db.query(TransformationPersonnel).filter(
            TransformationPersonnel.transformation_id == t_id,
            TransformationPersonnel.output_weight_considered.isnot(None),
        ).all()
        total_assigned = sum(p.output_weight_considered for p in personnel)
        if total_assigned > total_output:
            return "personnel_output_exceeded"

        obj.to_date = completion_date or datetime.now(timezone.utc)

        # ── Compute cost_per_kg for output batches ──────────────────────
        # IMPORTANT: Avoid double-counting:
        # - Personnel wages → also recorded as Labour expenses (via expense_id FK) — only count from TransformationPersonnel
        # - Vehicle fuel → also recorded as ConsumableConsumption with is_vehicle_fuel=True — only count from TransformationVehicle

        # 1. Personnel wages (frozen as total_wages_payable)
        personnel_cost = (
            self.db.query(func.coalesce(func.sum(TransformationPersonnel.total_wages_payable), 0))
            .filter(TransformationPersonnel.transformation_id == t_id)
            .scalar()
        )

        # 2. Vehicle fuel costs
        vehicle_cost = (
            self.db.query(func.coalesce(func.sum(TransformationVehicle.fuel_cost), 0))
            .filter(TransformationVehicle.transformation_id == t_id)
            .scalar()
        )

        # 3. Consumable costs EXCLUDING vehicle fuel (already counted in vehicle_cost)
        consumable_cost = (
            self.db.query(func.coalesce(func.sum(ConsumableConsumption.total_cost), 0))
            .filter(
                ConsumableConsumption.transformation_id == t_id,
                ConsumableConsumption.is_vehicle_fuel == False,
            )
            .scalar()
        )

        # 4. Other expenses EXCLUDING personnel wage expenses (already counted in personnel_cost)
        personnel_expense_ids = (
            self.db.query(TransformationPersonnel.expense_id)
            .filter(
                TransformationPersonnel.transformation_id == t_id,
                TransformationPersonnel.expense_id.isnot(None),
            )
        )
        expense_cost = (
            self.db.query(func.coalesce(func.sum(Expense.amount), 0))
            .filter(
                Expense.transformation_id == t_id,
                ~Expense.id.in_(personnel_expense_ids),
            )
            .scalar()
        )

        # 5. Input material cost (accumulated from parent batches)
        input_material_cost = sum(
            Decimal(str(inp.input_weight or 0)) * Decimal(str(inp.batch.cost_per_kg or 0))
            for inp in inputs
        )

        total_cost = Decimal(str(personnel_cost)) + Decimal(str(vehicle_cost)) + Decimal(str(consumable_cost)) + Decimal(str(expense_cost)) + input_material_cost

        # Partition outputs into non-waste and waste
        non_waste_outputs = [o for o in outputs if not (o.batch.stage and o.batch.stage.is_waste)]
        waste_outputs = [o for o in outputs if o.batch.stage and o.batch.stage.is_waste]

        non_waste_total = sum(o.output_weight for o in non_waste_outputs)

        if non_waste_total > 0:
            cost_per_kg = total_cost / Decimal(str(non_waste_total))
        else:
            cost_per_kg = Decimal("0")

        # Freeze cost_per_kg: non-waste batches get computed cost, waste batches get 0
        for out in non_waste_outputs:
            out.batch.cost_per_kg = cost_per_kg
        for out in waste_outputs:
            out.batch.cost_per_kg = Decimal("0")

        self.db.commit()
        return None

    def delete(self, t_id: int) -> Optional[str]:
        """Returns None on success, 'not_found', 'complete', or 'has_outputs'."""
        obj = self.db.query(Transformation).filter(Transformation.id == t_id).first()
        if not obj:
            return "not_found"
        if obj.to_date is not None:
            return "complete"
        output_count = self.db.query(TransformationOutput).filter(
            TransformationOutput.transformation_id == t_id
        ).count()
        if output_count > 0:
            return "has_outputs"
        self.db.delete(obj)
        self.db.commit()
        return None

    # ── Inputs ────────────────────────────────────────────────────────────────

    def add_input(self, t_id: int, batch_id: int, input_weight: Decimal) -> Optional[str]:
        transformation = self.db.query(Transformation).options(
            joinedload(Transformation.transformation_type)
        ).filter(Transformation.id == t_id).first()
        if not transformation:
            return "not_found"
        if transformation.to_date is not None:
            return "complete"
        # Block inputs for root transformation types
        if transformation.transformation_type and transformation.transformation_type.is_root:
            return "root_no_inputs"
        batch = self.db.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            return "batch_not_found"
        if input_weight > batch.remaining_weight_kg:
            return "weight_exceeded"

        inp = TransformationInput(
            transformation_id=t_id,
            batch_id=batch_id,
            input_weight=input_weight,
        )
        self.db.add(inp)

        # Deduct weight from source batch
        batch.remaining_weight_kg -= input_weight
        if batch.remaining_weight_kg <= 0:
            batch.is_depleted = True

        self.db.commit()
        return None

    def remove_input(self, t_id: int, input_id: int) -> Optional[str]:
        transformation = self.db.query(Transformation).filter(Transformation.id == t_id).first()
        if not transformation:
            return "not_found"
        if transformation.to_date is not None:
            return "complete"
        inp = self.db.query(TransformationInput).filter(
            TransformationInput.id == input_id,
            TransformationInput.transformation_id == t_id,
        ).first()
        if not inp:
            return "not_found"

        # Restore weight to source batch
        batch = self.db.query(Batch).filter(Batch.id == inp.batch_id).first()
        if batch:
            batch.remaining_weight_kg += inp.input_weight
            if batch.is_depleted:
                batch.is_depleted = False

        self.db.delete(inp)
        self.db.commit()
        return None

    # ── Outputs ───────────────────────────────────────────────────────────────

    def add_output(self, t_id: int, data: TransformationOutputCreate) -> Optional[str]:
        from ..models.batch import BatchParent

        transformation = self.db.query(Transformation).options(
            joinedload(Transformation.transformation_type)
        ).filter(Transformation.id == t_id).first()
        if not transformation:
            return "not_found"
        if transformation.to_date is not None:
            return "complete"

        inputs = self.db.query(TransformationInput).filter(
            TransformationInput.transformation_id == t_id
        ).all()

        # Input gate: non-root transformations require at least one input
        if not (transformation.transformation_type and transformation.transformation_type.is_root):
            if not inputs:
                return "non_root_no_inputs"

        # Determine plantation_id: only valid for root transformations
        plantation_id = None
        if transformation.transformation_type and transformation.transformation_type.is_root:
            plantation_id = data.plantation_id

        batch = Batch(
            batch_code=data.batch_code,
            stage_id=data.stage_id,
            initial_weight_kg=data.output_weight,
            remaining_weight_kg=data.output_weight,
            plantation_id=plantation_id,
            notes=data.notes,
            is_depleted=False,
        )
        self.db.add(batch)
        self.db.flush()

        out = TransformationOutput(
            transformation_id=t_id,
            batch_id=batch.id,
            output_weight=data.output_weight,
        )
        self.db.add(out)

        # Create batch_parents entries for all input batches
        for inp in inputs:
            bp = BatchParent(
                child_batch_id=batch.id,
                parent_batch_id=inp.batch_id,
            )
            self.db.add(bp)

        self.db.commit()
        return None

    def remove_output(self, t_id: int, output_id: int) -> Optional[str]:
        from ..models.batch import BatchParent

        transformation = self.db.query(Transformation).filter(Transformation.id == t_id).first()
        if not transformation:
            return "not_found"
        if transformation.to_date is not None:
            return "complete"
        out = self.db.query(TransformationOutput).filter(
            TransformationOutput.id == output_id,
            TransformationOutput.transformation_id == t_id,
        ).first()
        if not out:
            return "not_found"

        # Delete batch_parents entries for this output batch
        self.db.query(BatchParent).filter(
            BatchParent.child_batch_id == out.batch_id
        ).delete()

        batch = self.db.query(Batch).filter(Batch.id == out.batch_id).first()
        self.db.delete(out)
        if batch:
            self.db.delete(batch)
        self.db.commit()
        return None

    # ── Personnel ─────────────────────────────────────────────────────────────

    def assign_personnel(self, t_id: int, data: TransformationPersonnelCreate) -> Optional[str]:
        transformation = self.db.query(Transformation).filter(Transformation.id == t_id).first()
        if not transformation:
            return "not_found"
        if transformation.to_date is not None:
            return "complete"
        personnel = self.db.query(Personnel).filter(Personnel.id == data.personnel_id).first()
        if not personnel:
            return "personnel_not_found"

        calc_method = personnel.wage_type.calculation_method if personnel.wage_type else "DAILY"

        # Validate OUTPUT requires output_weight_considered
        if calc_method == "OUTPUT" and not data.output_weight_considered:
            return "output_weight_required"
        if calc_method == "DAILY" and not data.days_worked:
            return "days_worked_required"

        # Validate output_weight_considered doesn't exceed remaining assignable qty
        if data.output_weight_considered:
            total_output = sum(
                o.output_weight for o in self.db.query(TransformationOutput).filter(
                    TransformationOutput.transformation_id == t_id
                ).all()
            )
            already_assigned = sum(
                p.output_weight_considered or Decimal("0")
                for p in self.db.query(TransformationPersonnel).filter(
                    TransformationPersonnel.transformation_id == t_id,
                    TransformationPersonnel.output_weight_considered.isnot(None),
                ).all()
            )
            remaining = total_output - already_assigned
            if data.output_weight_considered > remaining:
                return "output_weight_exceeded"

        # Calculate base wage
        if calc_method == "OUTPUT":
            base_wage = personnel.current_rate * data.output_weight_considered
        elif calc_method == "DAILY":
            base_wage = personnel.current_rate * data.days_worked
        else:  # MONTHLY
            base_wage = Decimal("0")

        total_wages_payable = base_wage + (data.additional_payments or Decimal("0"))

        assignment = TransformationPersonnel(
            transformation_id=t_id,
            personnel_id=data.personnel_id,
            assignment_date=datetime.now(timezone.utc),
            wage_type_at_time_id=personnel.wage_type_id,
            rate_at_time=personnel.current_rate,
            days_worked=data.days_worked,
            output_weight_considered=data.output_weight_considered,
            additional_payments=data.additional_payments,
            additional_payments_description=data.additional_payments_description,
            base_wage=base_wage,
            total_wages_payable=total_wages_payable,
            is_paid=False,
            notes=data.notes,
        )
        self.db.add(assignment)
        self.db.commit()
        return None

    def update_personnel(self, t_id: int, tp_id: int, data: TransformationPersonnelUpdate) -> Optional[str]:
        transformation = self.db.query(Transformation).filter(Transformation.id == t_id).first()
        if not transformation:
            return "not_found"
        if transformation.to_date is not None:
            return "complete"
        tp = self.db.query(TransformationPersonnel).filter(
            TransformationPersonnel.id == tp_id,
            TransformationPersonnel.transformation_id == t_id,
        ).first()
        if not tp:
            return "not_found"

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(tp, field, value)

        # Recalculate wages
        calc_method = tp.wage_type.calculation_method if tp.wage_type else "DAILY"
        if calc_method == "OUTPUT" and tp.output_weight_considered:
            tp.base_wage = tp.rate_at_time * tp.output_weight_considered
        elif calc_method == "DAILY":
            tp.base_wage = tp.rate_at_time * (tp.days_worked or Decimal("0"))
        else:  # MONTHLY
            tp.base_wage = Decimal("0")

        tp.total_wages_payable = tp.base_wage + (tp.additional_payments or Decimal("0"))

        self.db.commit()
        return None

    def remove_personnel(self, t_id: int, tp_id: int) -> Optional[str]:
        transformation = self.db.query(Transformation).filter(Transformation.id == t_id).first()
        if not transformation:
            return "not_found"
        if transformation.to_date is not None:
            return "complete"
        tp = self.db.query(TransformationPersonnel).filter(
            TransformationPersonnel.id == tp_id,
            TransformationPersonnel.transformation_id == t_id,
        ).first()
        if not tp:
            return "not_found"
        self.db.delete(tp)
        self.db.commit()
        return None

    def mark_personnel_paid(self, t_id: int, tp_id: int) -> Optional[str]:
        """Mark personnel assignment as paid, create expense entry."""
        from ..models.expense import ExpenseCategory

        tp = self.db.query(TransformationPersonnel).filter(
            TransformationPersonnel.id == tp_id,
            TransformationPersonnel.transformation_id == t_id,
        ).first()
        if not tp:
            return "not_found"
        if tp.is_paid:
            return "already_paid"

        # Find Labour category
        labour_cat = self.db.query(ExpenseCategory).filter(
            ExpenseCategory.name == "Labour"
        ).first()
        if not labour_cat:
            return "labour_category_missing"

        expense = Expense(
            date=datetime.now(timezone.utc),
            amount=tp.total_wages_payable,
            category_id=labour_cat.id,
            transformation_id=t_id,
            personnel_id=tp.personnel_id,
            description=f"Wages for {tp.personnel.name if tp.personnel else 'Unknown'}"
        )
        self.db.add(expense)
        self.db.flush()

        tp.is_paid = True
        tp.expense_id = expense.id
        self.db.commit()
        return None

    def mark_personnel_unpaid(self, t_id: int, tp_id: int) -> Optional[str]:
        """Reverse wage payment — delete expense and reset is_paid."""
        tp = self.db.query(TransformationPersonnel).filter(
            TransformationPersonnel.id == tp_id,
            TransformationPersonnel.transformation_id == t_id,
        ).first()
        if not tp:
            return "not_found"
        if not tp.is_paid:
            return "not_paid"

        if tp.expense_id:
            expense = self.db.query(Expense).filter(Expense.id == tp.expense_id).first()
            if expense:
                self.db.delete(expense)

        tp.is_paid = False
        tp.expense_id = None
        self.db.commit()
        return None

    # ── Vehicles ──────────────────────────────────────────────────────────────

    def assign_vehicle(self, t_id: int, data: TransformationVehicleCreate, consumable_svc=None) -> Optional[str]:
        transformation = self.db.query(Transformation).filter(Transformation.id == t_id).first()
        if not transformation:
            return "not_found"
        if transformation.to_date is not None:
            return "complete"
        vehicle = self.db.query(Vehicle).filter(Vehicle.id == data.vehicle_id).first()
        if not vehicle:
            return "vehicle_not_found"

        fuel_cost = None
        consumption_id = None

        if vehicle.fuel_consumable_id and data.fuel_qty > 0 and consumable_svc:
            # Record fuel consumption via FIFO
            result = consumable_svc.record_consumption(
                consumable_id=vehicle.fuel_consumable_id,
                quantity_used=data.fuel_qty,
                transformation_id=t_id,
                consumption_date=datetime.now(timezone.utc),
                notes=f"Fuel for vehicle {vehicle.number}",
            )
            if isinstance(result, str):
                return result  # Error string like "insufficient_stock"

            from ..models.consumables import ConsumableConsumption
            self.db.flush()
            consumption = (
                self.db.query(ConsumableConsumption)
                .filter(
                    ConsumableConsumption.transformation_id == t_id,
                    ConsumableConsumption.consumable_id == vehicle.fuel_consumable_id,
                )
                .order_by(ConsumableConsumption.id.desc())
                .first()
            )
            if consumption:
                consumption.is_vehicle_fuel = True
                fuel_cost = consumption.total_cost
                consumption_id = consumption.id

        tv = TransformationVehicle(
            transformation_id=t_id,
            vehicle_id=data.vehicle_id,
            hours_used=data.hours_used,
            fuel_qty=data.fuel_qty,
            fuel_cost=fuel_cost,
            consumable_consumption_id=consumption_id,
            notes=data.notes,
        )
        self.db.add(tv)
        self.db.commit()
        return None

    def update_vehicle(self, t_id: int, tv_id: int, data: TransformationVehicleUpdate) -> Optional[str]:
        transformation = self.db.query(Transformation).filter(Transformation.id == t_id).first()
        if not transformation:
            return "not_found"
        if transformation.to_date is not None:
            return "complete"
        tv = self.db.query(TransformationVehicle).filter(
            TransformationVehicle.id == tv_id,
            TransformationVehicle.transformation_id == t_id,
        ).first()
        if not tv:
            return "not_found"
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(tv, field, value)
        self.db.commit()
        return None

    def remove_vehicle(self, t_id: int, tv_id: int) -> Optional[str]:
        from ..models.consumables import ConsumableConsumption, ConsumablePurchase, ConsumptionAllocation

        transformation = self.db.query(Transformation).filter(Transformation.id == t_id).first()
        if not transformation:
            return "not_found"
        if transformation.to_date is not None:
            return "complete"
        tv = self.db.query(TransformationVehicle).filter(
            TransformationVehicle.id == tv_id,
            TransformationVehicle.transformation_id == t_id,
        ).first()
        if not tv:
            return "not_found"

        # Reverse fuel consumption if linked
        if tv.consumable_consumption_id:
            consumption = self.db.query(ConsumableConsumption).filter(
                ConsumableConsumption.id == tv.consumable_consumption_id
            ).first()
            if consumption:
                allocations = self.db.query(ConsumptionAllocation).filter(
                    ConsumptionAllocation.consumption_id == consumption.id
                ).all()
                for alloc in allocations:
                    purchase = self.db.query(ConsumablePurchase).filter(
                        ConsumablePurchase.id == alloc.purchase_id
                    ).first()
                    if purchase:
                        purchase.remaining_quantity += alloc.quantity_allocated
                    self.db.delete(alloc)
                self.db.delete(consumption)

        self.db.delete(tv)
        self.db.commit()
        return None

    # ── Consumables ───────────────────────────────────────────────────────────

    def add_consumable(self, t_id: int, data: TransformationConsumableCreate, consumable_svc) -> Optional[str]:
        transformation = self.db.query(Transformation).filter(Transformation.id == t_id).first()
        if not transformation:
            return "not_found"
        if transformation.to_date is not None:
            return "complete"
        return consumable_svc.record_consumption(
            consumable_id=data.consumable_id,
            quantity_used=data.quantity_used,
            transformation_id=t_id,
            consumption_date=data.consumption_date,
            notes=data.notes,
        )

    def remove_consumable(self, t_id: int, tc_id: int) -> Optional[str]:
        """Remove consumption and reverse FIFO allocations."""
        from ..models.consumables import ConsumablePurchase, ConsumptionAllocation
        transformation = self.db.query(Transformation).filter(Transformation.id == t_id).first()
        if not transformation:
            return "not_found"
        if transformation.to_date is not None:
            return "complete"
        consumption = self.db.query(ConsumableConsumption).filter(
            ConsumableConsumption.id == tc_id,
            ConsumableConsumption.transformation_id == t_id,
        ).first()
        if not consumption:
            return "not_found"
        allocations = self.db.query(ConsumptionAllocation).filter(
            ConsumptionAllocation.consumption_id == tc_id
        ).all()
        for alloc in allocations:
            purchase = self.db.query(ConsumablePurchase).filter(
                ConsumablePurchase.id == alloc.purchase_id
            ).first()
            if purchase:
                purchase.remaining_quantity += alloc.quantity_allocated
            self.db.delete(alloc)
        self.db.delete(consumption)
        self.db.commit()
        return None

    # ── Expenses ──────────────────────────────────────────────────────────────

    def add_expense(self, t_id: int, data: TransformationExpenseCreate) -> Optional[str]:
        """Add a manual expense to a transformation."""
        from ..models.expense import ExpenseCategory

        transformation = self.db.query(Transformation).filter(Transformation.id == t_id).first()
        if not transformation:
            return "not_found"
        if transformation.to_date is not None:
            return "complete"

        category = self.db.query(ExpenseCategory).filter(
            ExpenseCategory.id == data.category_id
        ).first()
        if not category:
            return "category_not_found"

        expense = Expense(
            date=data.date,
            amount=data.amount,
            category_id=data.category_id,
            transformation_id=t_id,
            description=data.description,
        )
        self.db.add(expense)
        self.db.commit()
        return None

    def remove_expense(self, t_id: int, expense_id: int) -> Optional[str]:
        """Remove an expense from a transformation. Blocks deletion of wage expenses."""
        transformation = self.db.query(Transformation).filter(Transformation.id == t_id).first()
        if not transformation:
            return "not_found"
        if transformation.to_date is not None:
            return "complete"
        expense = self.db.query(Expense).filter(
            Expense.id == expense_id,
            Expense.transformation_id == t_id,
        ).first()
        if not expense:
            return "not_found"

        # Check if this expense is linked to a personnel wage payment
        wage_link = self.db.query(TransformationPersonnel).filter(
            TransformationPersonnel.expense_id == expense_id
        ).first()
        if wage_link:
            return "wage_expense_protected"

        self.db.delete(expense)
        self.db.commit()
        return None

    # ── Transformation Types ───────────────────────────────────────────────────

    def create_type(self, data) -> Optional[str]:
        """Create a transformation type. Validates is_root uniqueness."""
        if data.is_root:
            existing_root = self.db.query(TransformationType).filter(
                TransformationType.is_root == True
            ).first()
            if existing_root:
                return "root_already_exists"

        tt = TransformationType(
            name=data.name,
            is_root=data.is_root or False,
            description=data.description,
        )
        self.db.add(tt)
        self.db.commit()
        self.db.refresh(tt)
        return tt

    def update_type(self, type_id: int, data) -> Optional[str]:
        """Update a transformation type. Validates is_root uniqueness."""
        tt = self.db.query(TransformationType).filter(TransformationType.id == type_id).first()
        if not tt:
            return "not_found"

        if data.is_root:
            existing_root = self.db.query(TransformationType).filter(
                TransformationType.is_root == True,
                TransformationType.id != type_id,
            ).first()
            if existing_root:
                return "root_already_exists"

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(tt, field, value)
        self.db.commit()
        self.db.refresh(tt)
        return tt

    def delete_type(self, type_id: int) -> Optional[str]:
        """Delete a transformation type if no transformations reference it."""
        tt = self.db.query(TransformationType).filter(TransformationType.id == type_id).first()
        if not tt:
            return "not_found"
        in_use = self.db.query(Transformation).filter(
            Transformation.type_id == type_id
        ).first()
        if in_use:
            return "in_use"
        self.db.delete(tt)
        self.db.commit()
        return None
