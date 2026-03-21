from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..core.dependencies import get_current_user
from ..crud.dashboard import DashboardService
from ..database import get_db
from ..schemas.dashboard import DailyOutputItem, DashboardSummary, RecentActivityItem, YieldTrendItem

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/summary", response_model=DashboardSummary)
def get_summary(db: Session = Depends(get_db)):
    return DashboardService(db).get_summary()


@router.get("/yield-trend", response_model=list[YieldTrendItem])
def get_yield_trend(weeks: int = Query(8, ge=1, le=52), db: Session = Depends(get_db)):
    return DashboardService(db).get_yield_trend(weeks=weeks)


@router.get("/recent-activity", response_model=list[RecentActivityItem])
def get_recent_activity(db: Session = Depends(get_db)):
    return DashboardService(db).get_recent_activity()


@router.get("/daily-output", response_model=list[DailyOutputItem])
def get_daily_output(end_date: date = Query(None), db: Session = Depends(get_db)):
    return DashboardService(db).get_daily_output(end_date=end_date)
