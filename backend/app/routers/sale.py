from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..core.dependencies import get_current_user, roles_required
from ..crud.sale import SaleService
from ..database import get_db
from ..models.user import User
from ..schemas.sale import SaleCreate, SaleDetail, SaleListItem, SaleReject

router = APIRouter(
    prefix="/sales",
    tags=["sales"],
    dependencies=[Depends(get_current_user)],
)


def _to_list_item(sale) -> dict:
    return {
        "id": sale.id,
        "sale_date": sale.sale_date,
        "customer_name": sale.customer.name if sale.customer else "Unknown",
        "customer_phone": sale.customer.phone if sale.customer else "",
        "stage_name": sale.stage.name if sale.stage else "Unknown",
        "quantity_sold": sale.quantity_sold,
        "selling_price": sale.selling_price,
        "cost_of_goods_sold": sale.cost_of_goods_sold,
        "profit": sale.profit,
        "profit_margin": sale.profit_margin,
        "status": sale.status,
        "allocation_mode": sale.allocation_mode,
    }


def _to_detail(sale) -> dict:
    return {
        "id": sale.id,
        "sale_date": sale.sale_date,
        "quantity_sold": sale.quantity_sold,
        "selling_price": sale.selling_price,
        "cost_of_goods_sold": sale.cost_of_goods_sold,
        "profit": sale.profit,
        "profit_margin": sale.profit_margin,
        "unit_selling_price": sale.unit_selling_price,
        "status": sale.status,
        "allocation_mode": sale.allocation_mode,
        "invoice_number": sale.invoice_number,
        "notes": sale.notes,
        "rejection_reason": sale.rejection_reason,
        "created_at": sale.created_at,
        "updated_at": sale.updated_at,
        "reviewed_at": sale.reviewed_at,
        "customer_id": sale.customer.id if sale.customer else None,
        "customer_name": sale.customer.name if sale.customer else "Unknown",
        "customer_phone": sale.customer.phone if sale.customer else "",
        "customer_address": sale.customer.address if sale.customer else None,
        "customer_notes": sale.customer.notes if sale.customer else None,
        "stage_id": sale.stage.id if sale.stage else None,
        "stage_name": sale.stage.name if sale.stage else "Unknown",
        "created_by_name": sale.created_by.email if sale.created_by else None,
        "reviewed_by_name": sale.reviewed_by.email if sale.reviewed_by else None,
        "allocations": [
            {
                "id": a.id,
                "sale_id": a.sale_id,
                "batch_id": a.batch_id,
                "quantity_allocated": a.quantity_allocated,
                "cost_allocated": a.cost_allocated,
                "batch_code": a.batch.batch_code if a.batch else None,
                "batch_cost_per_kg": a.batch.cost_per_kg if a.batch else None,
            }
            for a in (sale.allocations or [])
        ],
    }


@router.get("/stages", response_model=list[dict])
def get_salable_stages(db: Session = Depends(get_db)):
    """List stages marked as salable."""
    stages = SaleService(db).get_salable_stages()
    return [{"id": s.id, "name": s.name} for s in stages]


@router.get("/batches", response_model=list[dict])
def get_salable_batches(
    stage_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """List available batches at a salable stage for allocation."""
    batches = SaleService(db).get_salable_batches(stage_id)
    return [
        {
            "id": b.id,
            "batch_code": b.batch_code,
            "remaining_weight_kg": float(b.remaining_weight_kg),
            "cost_per_kg": float(b.cost_per_kg) if b.cost_per_kg else 0,
            "created_at": b.created_at.isoformat(),
        }
        for b in batches
    ]


@router.get("/", response_model=list[SaleListItem])
def list_sales(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    stage_id: Optional[int] = Query(None),
    customer_q: Optional[str] = Query(None),
    sale_status: Optional[str] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    sales = SaleService(db).get_list(
        date_from=date_from,
        date_to=date_to,
        stage_id=stage_id,
        customer_q=customer_q,
        status=sale_status,
        skip=skip,
        limit=limit,
    )
    return [_to_list_item(s) for s in sales]


@router.get("/{sale_id}", response_model=SaleDetail)
def get_sale(sale_id: int, db: Session = Depends(get_db)):
    sale = SaleService(db).get_by_id(sale_id)
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return _to_detail(sale)


@router.post(
    "/",
    response_model=SaleDetail,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(roles_required("admin"))],
)
def create_sale(
    data: SaleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Admin creates a sale directly (status=COMPLETED)."""
    svc = SaleService(db)
    sale, error = svc.create_sale(data, user.id, is_admin=True)
    if error:
        raise HTTPException(status_code=422, detail=error)
    return _to_detail(svc.get_by_id(sale.id))


@router.post("/request", response_model=SaleDetail, status_code=status.HTTP_201_CREATED)
def request_sale(
    data: SaleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Non-admin submits a sale request (status=PENDING, reserves inventory)."""
    svc = SaleService(db)
    sale, error = svc.create_sale(data, user.id, is_admin=False)
    if error:
        raise HTTPException(status_code=422, detail=error)
    return _to_detail(svc.get_by_id(sale.id))


@router.put(
    "/{sale_id}/approve",
    response_model=SaleDetail,
    dependencies=[Depends(roles_required("admin"))],
)
def approve_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = SaleService(db)
    error = svc.approve(sale_id, user.id)
    if error == "not_found":
        raise HTTPException(status_code=404, detail="Sale not found")
    if error == "not_pending":
        raise HTTPException(status_code=422, detail="Sale is not in PENDING status")
    return _to_detail(svc.get_by_id(sale_id))


@router.put(
    "/{sale_id}/reject",
    response_model=SaleDetail,
    dependencies=[Depends(roles_required("admin"))],
)
def reject_sale(
    sale_id: int,
    data: SaleReject,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = SaleService(db)
    error = svc.reject(sale_id, user.id, data)
    if error == "not_found":
        raise HTTPException(status_code=404, detail="Sale not found")
    if error == "not_pending":
        raise HTTPException(status_code=422, detail="Sale is not in PENDING status")
    return _to_detail(svc.get_by_id(sale_id))


@router.delete(
    "/{sale_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(roles_required("admin"))],
)
def delete_sale(sale_id: int, db: Session = Depends(get_db)):
    svc = SaleService(db)
    error = svc.delete(sale_id)
    if error == "not_found":
        raise HTTPException(status_code=404, detail="Sale not found")
