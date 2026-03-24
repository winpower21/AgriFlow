"""
Report Analytics Schemas
=========================

Pydantic v2 response schemas for the 7 report domains:
Sales (lease impact), Batches, Transformations, Personnel,
Consumables, Expenses, Plantations.
"""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel

from .sale import SalesAnalyticsResponse


# ---------------------------------------------------------------------------
# 1. Sales — Lease Impact Extension
# ---------------------------------------------------------------------------

class LeaseImpactItem(BaseModel):
    plantation_id: int
    plantation_name: str
    lease_cost: Decimal
    total_harvest_kg: float
    lease_cost_per_kg: float
    impact_on_sold_goods: Decimal


class ReportsSalesAnalyticsResponse(BaseModel):
    sales_analytics: SalesAnalyticsResponse
    lease_cost_impact: list[LeaseImpactItem]
    total_lease_impact: Decimal
    lease_adjusted_profit: Decimal
    lease_adjusted_margin_pct: float


# ---------------------------------------------------------------------------
# 2. Batches
# ---------------------------------------------------------------------------

class BatchesKPIs(BaseModel):
    total_batches: int
    avg_cost_per_kg: float
    total_weight_kg: float
    depleted_count: int


class StageCostItem(BaseModel):
    stage_name: str
    avg_cost_per_kg: float
    batch_count: int


class CostTrendItem(BaseModel):
    period: str  # YYYY-MM
    avg_cost_per_kg: float


class CostBreakdown(BaseModel):
    input_cost: float
    labor_cost: float
    consumable_cost: float
    vehicle_cost: float
    expense_cost: float


class TopCostContributor(BaseModel):
    batch_code: str
    cost_per_kg: float
    breakdown: CostBreakdown


class BatchesAnalyticsResponse(BaseModel):
    kpis: BatchesKPIs
    avg_cost_by_stage: list[StageCostItem]
    cost_trend: list[CostTrendItem]
    top_cost_contributors: list[TopCostContributor]


# ---------------------------------------------------------------------------
# 3. Transformations
# ---------------------------------------------------------------------------

class TransformationsKPIs(BaseModel):
    total_transformations: int
    avg_completion_days: float
    total_cost: Decimal
    avg_cost: Decimal


class CompletionByType(BaseModel):
    type_name: str
    avg_days: float
    count: int


class CostByType(BaseModel):
    type_name: str
    avg_labor_cost: Decimal
    avg_consumable_cost: Decimal
    avg_total: Decimal


class ResourceUtilization(BaseModel):
    type_name: str
    avg_personnel_count: float
    avg_vehicle_hours: float


class ConsumableUsageByType(BaseModel):
    type_name: str
    consumable_name: str
    avg_quantity: float
    avg_cost: Decimal


class TransformationsAnalyticsResponse(BaseModel):
    kpis: TransformationsKPIs
    avg_completion_by_type: list[CompletionByType]
    avg_cost_by_type: list[CostByType]
    resource_utilization: list[ResourceUtilization]
    consumable_usage_by_type: list[ConsumableUsageByType]


# ---------------------------------------------------------------------------
# 4. Personnel
# ---------------------------------------------------------------------------

class PersonnelKPIs(BaseModel):
    total_wages_paid: Decimal
    avg_wage_per_transformation: Decimal
    total_output_kg: float
    active_personnel_count: int


class EfficiencyRankingItem(BaseModel):
    personnel_id: int
    personnel_name: str
    total_wages: Decimal
    total_output_kg: float
    cost_per_kg: float
    transformation_count: int


class PaymentOutputTrend(BaseModel):
    period: str  # YYYY-MM
    total_wages: Decimal
    total_output_kg: float
    cost_per_kg: float


class PersonnelAnalyticsResponse(BaseModel):
    kpis: PersonnelKPIs
    efficiency_ranking: list[EfficiencyRankingItem]
    payment_output_trend: list[PaymentOutputTrend]


# ---------------------------------------------------------------------------
# 5. Consumables
# ---------------------------------------------------------------------------

class ConsumablesKPIs(BaseModel):
    total_spend: Decimal
    total_items: int
    top_category: Optional[str] = None
    avg_utilization_rate: float


class UtilizationItem(BaseModel):
    consumable_id: int
    consumable_name: str
    purchased_qty: float
    consumed_qty: float
    utilization_rate: float


class CategoryCostItem(BaseModel):
    consumable_name: str
    cost: Decimal


class CategoryCostSpread(BaseModel):
    category_name: str
    total_cost: Decimal
    percentage: float
    items: list[CategoryCostItem]


class SpendOverTime(BaseModel):
    period: str  # YYYY-MM
    total_cost: Decimal


class ConsumablesAnalyticsResponse(BaseModel):
    kpis: ConsumablesKPIs
    utilization_by_item: list[UtilizationItem]
    category_cost_spread: list[CategoryCostSpread]
    spend_over_time: list[SpendOverTime]


# ---------------------------------------------------------------------------
# 6. Expenses
# ---------------------------------------------------------------------------

class ExpensesKPIs(BaseModel):
    total_expenses: Decimal
    avg_per_period: Decimal
    largest_category: Optional[str] = None
    expense_count: int


class CategoryDistribution(BaseModel):
    category_name: str
    total: Decimal
    percentage: float
    count: int


class TimeDistribution(BaseModel):
    period: str  # YYYY-MM
    total: Decimal
    count: int


class ExpensesAnalyticsResponse(BaseModel):
    kpis: ExpensesKPIs
    category_distribution: list[CategoryDistribution]
    time_distribution: list[TimeDistribution]


# ---------------------------------------------------------------------------
# 7. Plantations
# ---------------------------------------------------------------------------

class PlantationsKPIs(BaseModel):
    total_plantations: int
    active_count: int
    total_harvest_kg: float
    total_lease_cost: Decimal


class OutputOverTime(BaseModel):
    period: str  # YYYY-MM
    plantation_name: str
    harvest_kg: float


class LeasePeriod(BaseModel):
    period: str  # YYYY
    lease_cost: Decimal


class LeaseCostTrend(BaseModel):
    plantation_name: str
    has_long_lease: bool
    periods: list[LeasePeriod]


class LeaseToOutputRatio(BaseModel):
    plantation_name: str
    annual_lease_cost: Decimal
    annual_harvest_kg: float
    cost_per_kg: float


class LeaseToRevenueRatio(BaseModel):
    plantation_name: str
    annual_lease_cost: Decimal
    annual_revenue: Decimal
    ratio: float


class PlantationsAnalyticsResponse(BaseModel):
    kpis: PlantationsKPIs
    output_over_time: list[OutputOverTime]
    lease_cost_trends: list[LeaseCostTrend]
    lease_to_output_ratio: list[LeaseToOutputRatio]
    lease_to_revenue_ratio: list[LeaseToRevenueRatio]
