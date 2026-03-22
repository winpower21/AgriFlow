from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..core.dependencies import get_current_user, roles_required
from ..crud.consumable import ConsumableService
from ..crud.transformation import TransformationService
from ..database import get_db
from ..schemas.response import ApiResponse
from ..schemas.transformation import (
    TransformationConsumableCreate,
    TransformationCreate,
    TransformationExpenseCreate,
    TransformationInputCreate,
    TransformationListItem,
    TransformationOutputCreate,
    TransformationPersonnelCreate,
    TransformationPersonnelUpdate,
    TransformationSchema,
    TransformationTypeCreate,
    TransformationTypeSchema,
    TransformationTypeUpdate,
    TransformationUpdate,
    TransformationVehicleCreate,
    TransformationVehicleUpdate,
)

router = APIRouter(
    prefix="/transformations",
    tags=["transformations"],
    dependencies=[Depends(get_current_user)],
)

types_router = APIRouter(
    prefix="/transformation-types",
    tags=["transformation-types"],
    dependencies=[Depends(get_current_user)],
)


def _calc_remaining_assignable(t) -> Optional[Decimal]:
    from decimal import Decimal
    outputs = t.outputs or []
    if not outputs:
        return None
    total_output = sum((o.output_weight for o in outputs), Decimal("0"))
    already_assigned = sum(
        (p.output_weight_considered or Decimal("0"))
        for p in (t.personnel_assignments or [])
    )
    return total_output - already_assigned


def _serialize(t) -> dict:
    return {
        "id": t.id,
        "type_id": t.type_id,
        "from_date": t.from_date,
        "to_date": t.to_date,
        "notes": t.notes,
        "created_at": t.created_at,
        "updated_at": t.updated_at,
        "transformation_type": {
            "id": t.transformation_type.id,
            "name": t.transformation_type.name,
            "is_root": t.transformation_type.is_root,
            "description": t.transformation_type.description,
        } if t.transformation_type else {"id": t.type_id, "name": "Unknown", "is_root": False, "description": None},
        "inputs": [
            {
                "id": i.id,
                "transformation_id": i.transformation_id,
                "batch_id": i.batch_id,
                "batch_code": i.batch.batch_code if i.batch else None,
                "stage_name": i.batch.stage.name if i.batch and i.batch.stage else None,
                "input_weight": i.input_weight,
            }
            for i in (t.inputs or [])
        ],
        "outputs": [
            {
                "id": o.id,
                "transformation_id": o.transformation_id,
                "batch_id": o.batch_id,
                "batch_code": o.batch.batch_code if o.batch else None,
                "stage_name": o.batch.stage.name if o.batch and o.batch.stage else None,
                "output_weight": o.output_weight,
            }
            for o in (t.outputs or [])
        ],
        "personnel_assignments": [
            {
                "id": p.id,
                "transformation_id": p.transformation_id,
                "personnel_id": p.personnel_id,
                "personnel_name": p.personnel.name if p.personnel else None,
                "assignment_date": p.assignment_date,
                "wage_type_at_time_id": p.wage_type_at_time_id,
                "wage_type_name": p.wage_type.name if p.wage_type else None,
                "rate_at_time": p.rate_at_time,
                "days_worked": p.days_worked,
                "output_weight_considered": p.output_weight_considered,
                "additional_payments": p.additional_payments,
                "additional_payments_description": p.additional_payments_description,
                "base_wage": p.base_wage,
                "total_wages_payable": p.total_wages_payable,
                "is_paid": p.is_paid,
                "expense_id": p.expense_id,
                "notes": p.notes,
                "created_at": p.created_at,
            }
            for p in (t.personnel_assignments or [])
        ],
        "vehicle_usage": [
            {
                "id": v.id,
                "transformation_id": v.transformation_id,
                "vehicle_id": v.vehicle_id,
                "vehicle_number": v.vehicle.number if v.vehicle else None,
                "vehicle_type": v.vehicle.vehicle_type if v.vehicle else None,
                "fuel_consumable_name": (
                    v.vehicle.fuel_consumable.name
                    if v.vehicle and v.vehicle.fuel_consumable else None
                ),
                "hours_used": v.hours_used,
                "fuel_qty": v.fuel_qty,
                "fuel_cost": v.fuel_cost,
                "notes": v.notes,
            }
            for v in (t.vehicle_usage or [])
        ],
        "consumable_consumptions": [
            {
                "id": c.id,
                "transformation_id": c.transformation_id,
                "consumable_id": c.consumable_id,
                "consumable_name": c.consumable.name if c.consumable else None,
                "consumable_unit": c.consumable.unit if c.consumable else None,
                "consumption_date": c.consumption_date,
                "quantity_used": c.quantity_used,
                "total_cost": c.total_cost,
                "notes": c.notes,
                "created_at": c.created_at,
            }
            for c in (t.consumable_consumptions or [])
            if not c.is_vehicle_fuel  # Exclude fuel — shown in vehicle section
        ],
        "expenses": [
            {
                "id": e.id,
                "date": e.date,
                "amount": e.amount,
                "category_id": e.category_id,
                "category_name": e.category.name if e.category else None,
                "description": e.description,
                "transformation_id": e.transformation_id,
                "is_wage_expense": any(
                    tp.expense_id == e.id
                    for tp in (t.personnel_assignments or [])
                ),
            }
            for e in (t.expenses or [])
        ],
        "remaining_assignable_output_qty": _calc_remaining_assignable(t),
    }


def _serialize_list(t) -> dict:
    from decimal import Decimal
    input_codes = [i.batch.batch_code for i in t.inputs if i.batch] if t.inputs else []
    total_in = sum((i.input_weight for i in t.inputs), Decimal("0")) if t.inputs else None
    return {
        "id": t.id,
        "type_id": t.type_id,
        "type_name": t.transformation_type.name if t.transformation_type else None,
        "from_date": t.from_date,
        "to_date": t.to_date,
        "notes": t.notes,
        "is_complete": t.to_date is not None,
        "input_batch_codes": input_codes,
        "total_input_weight": total_in if total_in else None,
        "created_at": t.created_at,
    }


@types_router.get("/", response_model=ApiResponse[list[TransformationTypeSchema]])
def list_transformation_types(db: Session = Depends(get_db)):
    return ApiResponse(data=TransformationService(db).get_types())


@types_router.post("/", status_code=201, response_model=ApiResponse[TransformationTypeSchema],
                   dependencies=[Depends(roles_required("admin"))])
def create_transformation_type(data: TransformationTypeCreate, db: Session = Depends(get_db)):
    result = TransformationService(db).create_type(data)
    if result == "root_already_exists":
        raise HTTPException(status_code=409, detail="A root transformation type already exists")
    return ApiResponse(data=result, message="Transformation type created", type="success")


@types_router.put("/{type_id}", response_model=ApiResponse[TransformationTypeSchema],
                  dependencies=[Depends(roles_required("admin"))])
def update_transformation_type(type_id: int, data: TransformationTypeUpdate, db: Session = Depends(get_db)):
    result = TransformationService(db).update_type(type_id, data)
    if result == "not_found":
        raise HTTPException(status_code=404, detail="Transformation type not found")
    if result == "root_already_exists":
        raise HTTPException(status_code=409, detail="A root transformation type already exists")
    return ApiResponse(data=result, message="Transformation type updated", type="success")


@types_router.delete("/{type_id}", response_model=ApiResponse[None],
                     dependencies=[Depends(roles_required("admin"))])
def delete_transformation_type(type_id: int, db: Session = Depends(get_db)):
    result = TransformationService(db).delete_type(type_id)
    if result == "not_found":
        raise HTTPException(status_code=404, detail="Transformation type not found")
    if result == "in_use":
        raise HTTPException(status_code=409, detail="Cannot delete: type is used by transformations")
    return ApiResponse(data=None, message="Transformation type deleted", type="success")


@router.get("/", response_model=ApiResponse[list[TransformationListItem]])
def list_transformations(
    type_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
):
    items = TransformationService(db).get_all(
        type_id=type_id, status=status, date_from=date_from, date_to=date_to
    )
    return ApiResponse(data=[_serialize_list(t) for t in items])


@router.post("/", status_code=201, response_model=ApiResponse[TransformationSchema],
             dependencies=[Depends(roles_required("admin"))])
def create_transformation(data: TransformationCreate, db: Session = Depends(get_db)):
    t = TransformationService(db).create(data)
    return ApiResponse(data=_serialize(t), message="Transformation created successfully", type="success")


@router.get("/{t_id}", response_model=ApiResponse[TransformationSchema])
def get_transformation(t_id: int, db: Session = Depends(get_db)):
    t = TransformationService(db).get_by_id(t_id)
    if not t:
        raise HTTPException(status_code=404, detail="Transformation not found")
    return ApiResponse(data=_serialize(t))


@router.put("/{t_id}", response_model=ApiResponse[TransformationSchema],
            dependencies=[Depends(roles_required("admin"))])
def update_transformation(t_id: int, data: TransformationUpdate, db: Session = Depends(get_db)):
    t = TransformationService(db).update(t_id, data)
    if not t:
        raise HTTPException(status_code=404, detail="Transformation not found")
    return ApiResponse(data=_serialize(t), message="Transformation updated successfully", type="success")


@router.post("/{t_id}/complete", response_model=ApiResponse[TransformationSchema],
             dependencies=[Depends(roles_required("admin"))])
def complete_transformation(t_id: int, db: Session = Depends(get_db)):
    svc = TransformationService(db)
    result = svc.complete(t_id)
    if result == "not_found":
        raise HTTPException(status_code=404, detail="Transformation not found")
    if result == "no_outputs":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot complete: transformation has no output batches",
        )
    if result == "personnel_output_exceeded":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot complete: sum of output_weight_considered exceeds total output weight",
        )
    return ApiResponse(data=_serialize(svc.get_by_id(t_id)), message="Transformation marked as complete", type="success")


@router.delete("/{t_id}", response_model=ApiResponse[None],
               dependencies=[Depends(roles_required("admin"))])
def delete_transformation(t_id: int, db: Session = Depends(get_db)):
    result = TransformationService(db).delete(t_id)
    if result == "not_found":
        raise HTTPException(status_code=404, detail="Transformation not found")
    if result == "has_outputs":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete: transformation has output batches",
        )
    return ApiResponse(data=None, message="Transformation deleted successfully", type="success")


# ── Inputs ────────────────────────────────────────────────────────────────────

@router.post("/{t_id}/inputs", status_code=201, response_model=ApiResponse[TransformationSchema],
             dependencies=[Depends(roles_required("admin"))])
def add_input(t_id: int, data: TransformationInputCreate, db: Session = Depends(get_db)):
    svc = TransformationService(db)
    result = svc.add_input(t_id, data.batch_id, data.input_weight)
    if result == "not_found":
        raise HTTPException(status_code=404, detail="Transformation not found")
    if result == "complete":
        raise HTTPException(status_code=409, detail="Cannot modify a completed transformation")
    if result == "batch_not_found":
        raise HTTPException(status_code=404, detail="Batch not found")
    if result == "weight_exceeded":
        raise HTTPException(status_code=422, detail="input_weight exceeds batch remaining_weight_kg")
    if result == "root_no_inputs":
        raise HTTPException(status_code=422, detail="Root transformation types do not accept inputs")
    return ApiResponse(data=_serialize(svc.get_by_id(t_id)), message="Input batch added", type="success")


@router.delete("/{t_id}/inputs/{input_id}", response_model=ApiResponse[None],
               dependencies=[Depends(roles_required("admin"))])
def remove_input(t_id: int, input_id: int, db: Session = Depends(get_db)):
    result = TransformationService(db).remove_input(t_id, input_id)
    if result == "not_found":
        raise HTTPException(status_code=404, detail="Not found")
    if result == "complete":
        raise HTTPException(status_code=409, detail="Cannot modify a completed transformation")
    return ApiResponse(data=None, message="Input batch removed", type="success")


# ── Outputs ───────────────────────────────────────────────────────────────────

@router.post("/{t_id}/outputs", status_code=201, response_model=ApiResponse[TransformationSchema],
             dependencies=[Depends(roles_required("admin"))])
def add_output(t_id: int, data: TransformationOutputCreate, db: Session = Depends(get_db)):
    svc = TransformationService(db)
    result = svc.add_output(t_id, data)
    if result == "not_found":
        raise HTTPException(status_code=404, detail="Transformation not found")
    if result == "complete":
        raise HTTPException(status_code=409, detail="Cannot modify a completed transformation")
    return ApiResponse(data=_serialize(svc.get_by_id(t_id)), message="Output batch added", type="success")


@router.delete("/{t_id}/outputs/{output_id}", response_model=ApiResponse[None],
               dependencies=[Depends(roles_required("admin"))])
def remove_output(t_id: int, output_id: int, db: Session = Depends(get_db)):
    result = TransformationService(db).remove_output(t_id, output_id)
    if result == "not_found":
        raise HTTPException(status_code=404, detail="Not found")
    if result == "complete":
        raise HTTPException(status_code=409, detail="Cannot modify a completed transformation")
    return ApiResponse(data=None, message="Output batch removed", type="success")


# ── Personnel ─────────────────────────────────────────────────────────────────

@router.post("/{t_id}/personnel", status_code=201, response_model=ApiResponse[TransformationSchema],
             dependencies=[Depends(roles_required("admin"))])
def assign_personnel(t_id: int, data: TransformationPersonnelCreate, db: Session = Depends(get_db)):
    svc = TransformationService(db)
    result = svc.assign_personnel(t_id, data)
    if result == "not_found":
        raise HTTPException(status_code=404, detail="Transformation not found")
    if result == "personnel_not_found":
        raise HTTPException(status_code=404, detail="Personnel not found")
    if result == "output_weight_required":
        raise HTTPException(status_code=422, detail="PER_KG wage type requires output_weight_considered")
    if result == "output_weight_exceeded":
        raise HTTPException(status_code=422, detail="output_weight_considered exceeds remaining assignable output quantity")
    return ApiResponse(data=_serialize(svc.get_by_id(t_id)), message="Personnel assigned", type="success")


@router.put("/{t_id}/personnel/{tp_id}", response_model=ApiResponse[TransformationSchema],
            dependencies=[Depends(roles_required("admin"))])
def update_personnel(t_id: int, tp_id: int, data: TransformationPersonnelUpdate,
                     db: Session = Depends(get_db)):
    svc = TransformationService(db)
    result = svc.update_personnel(t_id, tp_id, data)
    if result == "not_found":
        raise HTTPException(status_code=404, detail="Assignment not found")
    return ApiResponse(data=_serialize(svc.get_by_id(t_id)), message="Personnel assignment updated", type="success")


@router.delete("/{t_id}/personnel/{tp_id}", response_model=ApiResponse[None],
               dependencies=[Depends(roles_required("admin"))])
def remove_personnel(t_id: int, tp_id: int, db: Session = Depends(get_db)):
    result = TransformationService(db).remove_personnel(t_id, tp_id)
    if result == "not_found":
        raise HTTPException(status_code=404, detail="Assignment not found")
    return ApiResponse(data=None, message="Personnel removed", type="success")


@router.post("/{t_id}/personnel/{tp_id}/mark-paid", response_model=ApiResponse[TransformationSchema],
             dependencies=[Depends(roles_required("admin"))])
def mark_personnel_paid(t_id: int, tp_id: int, db: Session = Depends(get_db)):
    svc = TransformationService(db)
    result = svc.mark_personnel_paid(t_id, tp_id)
    if result == "not_found":
        raise HTTPException(status_code=404, detail="Assignment not found")
    if result == "already_paid":
        raise HTTPException(status_code=409, detail="Already marked as paid")
    if result == "labour_category_missing":
        raise HTTPException(status_code=500, detail="Labour expense category not found")
    return ApiResponse(data=_serialize(svc.get_by_id(t_id)), message="Personnel marked as paid", type="success")


@router.post("/{t_id}/personnel/{tp_id}/mark-unpaid", response_model=ApiResponse[TransformationSchema],
             dependencies=[Depends(roles_required("admin"))])
def mark_personnel_unpaid(t_id: int, tp_id: int, db: Session = Depends(get_db)):
    svc = TransformationService(db)
    result = svc.mark_personnel_unpaid(t_id, tp_id)
    if result == "not_found":
        raise HTTPException(status_code=404, detail="Assignment not found")
    if result == "not_paid":
        raise HTTPException(status_code=409, detail="Not currently marked as paid")
    return ApiResponse(data=_serialize(svc.get_by_id(t_id)), message="Personnel marked as unpaid", type="success")


# ── Vehicles ──────────────────────────────────────────────────────────────────

@router.post("/{t_id}/vehicles", status_code=201, response_model=ApiResponse[TransformationSchema],
             dependencies=[Depends(roles_required("admin"))])
def assign_vehicle(t_id: int, data: TransformationVehicleCreate, db: Session = Depends(get_db)):
    svc = TransformationService(db)
    result = svc.assign_vehicle(t_id, data, ConsumableService(db))
    if result == "not_found":
        raise HTTPException(status_code=404, detail="Transformation not found")
    if result == "vehicle_not_found":
        raise HTTPException(status_code=404, detail="Vehicle not found")
    if result == "insufficient_stock":
        raise HTTPException(status_code=422, detail="Insufficient fuel stock to fulfill this vehicle assignment")
    if result == "consumable_not_found":
        raise HTTPException(status_code=404, detail="Fuel consumable not found")
    return ApiResponse(data=_serialize(svc.get_by_id(t_id)), message="Vehicle assigned", type="success")


@router.put("/{t_id}/vehicles/{tv_id}", response_model=ApiResponse[TransformationSchema],
            dependencies=[Depends(roles_required("admin"))])
def update_vehicle(t_id: int, tv_id: int, data: TransformationVehicleUpdate,
                   db: Session = Depends(get_db)):
    svc = TransformationService(db)
    result = svc.update_vehicle(t_id, tv_id, data)
    if result == "not_found":
        raise HTTPException(status_code=404, detail="Vehicle assignment not found")
    return ApiResponse(data=_serialize(svc.get_by_id(t_id)), message="Vehicle assignment updated", type="success")


@router.delete("/{t_id}/vehicles/{tv_id}", response_model=ApiResponse[None],
               dependencies=[Depends(roles_required("admin"))])
def remove_vehicle(t_id: int, tv_id: int, db: Session = Depends(get_db)):
    result = TransformationService(db).remove_vehicle(t_id, tv_id)
    if result == "not_found":
        raise HTTPException(status_code=404, detail="Vehicle assignment not found")
    return ApiResponse(data=None, message="Vehicle removed", type="success")


# ── Consumables ───────────────────────────────────────────────────────────────

@router.post("/{t_id}/consumables", status_code=201, response_model=ApiResponse[TransformationSchema],
             dependencies=[Depends(roles_required("admin"))])
def add_consumable(t_id: int, data: TransformationConsumableCreate, db: Session = Depends(get_db)):
    svc = TransformationService(db)
    result = svc.add_consumable(t_id, data, ConsumableService(db))
    if result == "not_found":
        raise HTTPException(status_code=404, detail="Transformation not found")
    if result == "consumable_not_found":
        raise HTTPException(status_code=404, detail="Consumable not found")
    if result == "insufficient_stock":
        raise HTTPException(status_code=422, detail="Insufficient stock to fulfill this consumption")
    return ApiResponse(data=_serialize(svc.get_by_id(t_id)), message="Consumable added", type="success")


@router.delete("/{t_id}/consumables/{tc_id}", response_model=ApiResponse[None],
               dependencies=[Depends(roles_required("admin"))])
def remove_consumable(t_id: int, tc_id: int, db: Session = Depends(get_db)):
    result = TransformationService(db).remove_consumable(t_id, tc_id)
    if result == "not_found":
        raise HTTPException(status_code=404, detail="Consumable usage not found")
    return ApiResponse(data=None, message="Consumable removed", type="success")


# ── Expenses ─────────────────────────────────────────────────────────────────

@router.post("/{t_id}/expenses", status_code=201, response_model=ApiResponse[TransformationSchema],
             dependencies=[Depends(roles_required("admin"))])
def add_expense(t_id: int, data: TransformationExpenseCreate, db: Session = Depends(get_db)):
    svc = TransformationService(db)
    result = svc.add_expense(t_id, data)
    if result == "not_found":
        raise HTTPException(status_code=404, detail="Transformation not found")
    if result == "category_not_found":
        raise HTTPException(status_code=404, detail="Expense category not found")
    return ApiResponse(data=_serialize(svc.get_by_id(t_id)), message="Expense added", type="success")


@router.delete("/{t_id}/expenses/{expense_id}", response_model=ApiResponse[None],
               dependencies=[Depends(roles_required("admin"))])
def remove_expense(t_id: int, expense_id: int, db: Session = Depends(get_db)):
    result = TransformationService(db).remove_expense(t_id, expense_id)
    if result == "not_found":
        raise HTTPException(status_code=404, detail="Expense not found")
    if result == "wage_expense_protected":
        raise HTTPException(status_code=409,
                            detail="Cannot delete wage expense directly. Use mark-unpaid instead.")
    return ApiResponse(data=None, message="Expense removed", type="success")
