"""
Dashboard Pydantic schemas.
"""
from typing import List, Optional

from pydantic import BaseModel


class StageSummaryItem(BaseModel):
    stage_id: int
    stage_name: str
    batch_count: int
    total_remaining_kg: float
    icon: str | None = None
    color: str | None = None


class DashboardSummary(BaseModel):
    stages: List[StageSummaryItem]
    active_transformation_count: int
    total_kg_in_pipeline: float
    avg_yield_rate_30d: Optional[float] = None


class YieldTrendItem(BaseModel):
    week_label: str  # e.g. "2026-W10"
    total_output_kg: float


class RecentActivityItem(BaseModel):
    event_type: str   # "harvest", "transformation_complete"
    description: str
    date: str
    entity_id: int
    entity_type: str  # "batch" or "transformation"


class DailyStageOutput(BaseModel):
    stage_name: str
    stage_color: Optional[str] = None
    output_kg: float


class DailyOutputItem(BaseModel):
    date_label: str  # e.g. "Mar 14"
    total_output_kg: float
    stages: List[DailyStageOutput] = []
