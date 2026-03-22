"""
Reports Router
===============

Provides 7 analytics endpoints for the Reports page, one per domain tab.
All endpoints require JWT authentication.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..core.dependencies import get_current_user, roles_required
from ..crud.reports import ReportsService
from ..crud.sale import SaleService
from ..crud.user import UserService
from ..database import get_db
from ..models.user import User
from ..schemas.reports import (
    BatchesAnalyticsResponse,
    ConsumablesAnalyticsResponse,
    ExpensesAnalyticsResponse,
    PersonnelAnalyticsResponse,
    PlantationsAnalyticsResponse,
    ReportsSalesAnalyticsResponse,
    TransformationsAnalyticsResponse,
)
from ..schemas.response import ApiResponse

router = APIRouter(
    prefix="/reports",
    tags=["reports"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/sales/analytics", response_model=ApiResponse[ReportsSalesAnalyticsResponse])
def get_sales_analytics(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    stage_id: Optional[int] = Query(None),
    customer_q: Optional[str] = Query(None),
    sale_status: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Sales analytics with lease cost impact overlay."""
    is_admin = "admin" in UserService(db).get_user_roles(user_or_id=user)
    sales_data = SaleService(db).get_analytics(
        date_from=date_from,
        date_to=date_to,
        stage_id=stage_id,
        customer_q=customer_q,
        status=sale_status,
        is_admin=is_admin,
    )
    lease_impact = ReportsService(db).get_sales_lease_impact(
        date_from=date_from,
        date_to=date_to,
        stage_id=stage_id,
        customer_q=customer_q,
        status=sale_status,
    )
    return ApiResponse(data=ReportsSalesAnalyticsResponse(
        sales_analytics=sales_data,
        **lease_impact,
    ))


@router.get("/batches/analytics", response_model=ApiResponse[BatchesAnalyticsResponse])
def get_batches_analytics(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    stage_id: Optional[int] = Query(None),
    plantation_id: Optional[int] = Query(None),
    is_depleted: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    """Batch analytics: cost trends, stage breakdown, top contributors."""
    return ApiResponse(data=ReportsService(db).get_batches_analytics(
        date_from=date_from,
        date_to=date_to,
        stage_id=stage_id,
        plantation_id=plantation_id,
        is_depleted=is_depleted,
    ))


@router.get("/transformations/analytics", response_model=ApiResponse[TransformationsAnalyticsResponse])
def get_transformations_analytics(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    type_id: Optional[int] = Query(None),
    transformation_status: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
):
    """Transformation analytics: completion times, costs, resource utilization."""
    return ApiResponse(data=ReportsService(db).get_transformations_analytics(
        date_from=date_from,
        date_to=date_to,
        type_id=type_id,
        status=transformation_status,
    ))


@router.get("/personnel/analytics", response_model=ApiResponse[PersonnelAnalyticsResponse])
def get_personnel_analytics(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    personnel_id: Optional[int] = Query(None),
    type_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Personnel analytics: efficiency ranking, payment trends."""
    return ApiResponse(data=ReportsService(db).get_personnel_analytics(
        date_from=date_from,
        date_to=date_to,
        personnel_id=personnel_id,
        type_id=type_id,
    ))


@router.get("/consumables/analytics", response_model=ApiResponse[ConsumablesAnalyticsResponse])
def get_consumables_analytics(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    category_id: Optional[int] = Query(None),
    consumable_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Consumables analytics: utilization, category spread, spend trends."""
    return ApiResponse(data=ReportsService(db).get_consumables_analytics(
        date_from=date_from,
        date_to=date_to,
        category_id=category_id,
        consumable_id=consumable_id,
    ))


@router.get("/expenses/analytics", response_model=ApiResponse[ExpensesAnalyticsResponse])
def get_expenses_analytics(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    category_id: Optional[int] = Query(None),
    plantation_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Expense analytics: category distribution, time trends."""
    return ApiResponse(data=ReportsService(db).get_expenses_analytics(
        date_from=date_from,
        date_to=date_to,
        category_id=category_id,
        plantation_id=plantation_id,
    ))


@router.get("/plantations/analytics", response_model=ApiResponse[PlantationsAnalyticsResponse])
def get_plantations_analytics(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    plantation_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    """Plantation analytics: output, lease costs, ratios."""
    return ApiResponse(data=ReportsService(db).get_plantations_analytics(
        date_from=date_from,
        date_to=date_to,
        plantation_id=plantation_id,
        is_active=is_active,
    ))
