from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ..core.dependencies import get_current_user, roles_required
from ..crud.consumable import ConsumableService
from ..database import get_db
from ..schemas.consumable import (
    ConsumableCategoryCreate, ConsumableCategorySchema,
    ConsumableCreate, ConsumableSchema, ConsumableUpdate,
    ConsumablePurchaseCreate, ConsumablePurchaseSchema, ConsumableWithStockSchema,
)

router = APIRouter(
    prefix="/consumables",
    tags=["consumables"],
    dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[ConsumableWithStockSchema])
def get_consumables(
    search: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    service = ConsumableService(db)
    items = service.get_all(search=search, category_id=category_id)
    result = []
    for item in items:
        totals = service.get_stock_totals(item.id)
        schema = ConsumableWithStockSchema.model_validate(item)
        schema.total_purchased = totals["total_purchased"]
        schema.total_remaining = totals["total_remaining"]
        result.append(schema)
    return result


@router.post("/", response_model=ConsumableSchema, status_code=201,
             dependencies=[Depends(roles_required("admin"))])
def create_consumable(data: ConsumableCreate, db: Session = Depends(get_db)):
    return ConsumableService(db).create(data)


@router.put("/{consumable_id}", response_model=ConsumableSchema,
            dependencies=[Depends(roles_required("admin"))])
def update_consumable(consumable_id: int, data: ConsumableUpdate, db: Session = Depends(get_db)):
    result = ConsumableService(db).update(consumable_id, data)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consumable not found")
    return result


@router.delete("/{consumable_id}", status_code=204,
               dependencies=[Depends(roles_required("admin"))])
def delete_consumable(consumable_id: int, db: Session = Depends(get_db)):
    result = ConsumableService(db).delete_consumable(consumable_id)
    if result == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consumable not found")
    if result == "has_consumptions":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete: this item has been used in consumptions",
        )


@router.get("/purchases", response_model=list[ConsumablePurchaseSchema])
def get_all_purchases(consumable_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    return ConsumableService(db).get_all_purchases(consumable_id=consumable_id)


@router.delete("/purchases/{purchase_id}", status_code=204,
               dependencies=[Depends(roles_required("admin"))])
def delete_purchase(purchase_id: int, db: Session = Depends(get_db)):
    result = ConsumableService(db).delete_purchase(purchase_id)
    if result == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase not found")
    if result == "has_allocations":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete: purchase has already been partially or fully consumed",
        )


@router.get("/{consumable_id}/purchases", response_model=list[ConsumablePurchaseSchema])
def get_purchases(consumable_id: int, db: Session = Depends(get_db)):
    return ConsumableService(db).get_purchases(consumable_id)


@router.post("/{consumable_id}/purchases", response_model=ConsumablePurchaseSchema, status_code=201,
             dependencies=[Depends(roles_required("admin"))])
def add_purchase(consumable_id: int, data: ConsumablePurchaseCreate, db: Session = Depends(get_db)):
    result = ConsumableService(db).add_purchase(consumable_id, data)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consumable not found")
    return result


# ── Categories sub-router ──────────────────────────────────────────────────────
categories_router = APIRouter(
    prefix="/consumable-categories",
    tags=["consumable-categories"],
    dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)


@categories_router.get("/", response_model=list[ConsumableCategorySchema])
def get_categories(db: Session = Depends(get_db)):
    return ConsumableService(db).get_all_categories()


@categories_router.post("/", response_model=ConsumableCategorySchema, status_code=201,
                        dependencies=[Depends(roles_required("admin"))])
def create_category(data: ConsumableCategoryCreate, db: Session = Depends(get_db)):
    return ConsumableService(db).create_category(data)


@categories_router.delete("/{category_id}", status_code=204,
                          dependencies=[Depends(roles_required("admin"))])
def delete_category(category_id: int, db: Session = Depends(get_db)):
    if not ConsumableService(db).delete_category(category_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
