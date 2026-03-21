"""
Reports CRUD Service
=====================

Provides aggregated analytics queries for 7 report domains:
Batches, Transformations, Personnel, Consumables, Expenses,
Plantations, and Sales (lease impact).

Usage:
    service = ReportsService(db)
    result = service.get_batches_analytics(date_from, date_to)
"""

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal as D
from typing import Optional

from sqlalchemy import and_, case, distinct, extract, func, or_
from sqlalchemy.orm import Session, aliased, joinedload

from ..models.batch import Batch, BatchParent, BatchStage
from ..models.consumables import (
    Consumable,
    ConsumableCategory,
    ConsumableConsumption,
    ConsumablePurchase,
)
from ..models.customer import Customer
from ..models.expense import Expense, ExpenseCategory
from ..models.personnel import Personnel, TransformationPersonnel
from ..models.plantation import Plantation, PlantationLease
from ..models.sales import Sale, SaleAllocation
from ..models.transformation import (
    Transformation,
    TransformationInput,
    TransformationOutput,
    TransformationType,
)
from ..models.vehicle import TransformationVehicle


class ReportsService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _date_filters(column, date_from, date_to):
        """Build date range filters, skipping None values."""
        filters = []
        if date_from is not None:
            filters.append(column >= date_from)
        if date_to is not None:
            filters.append(column <= date_to)
        return filters

    # -----------------------------------------------------------------------
    # Batches Analytics
    # -----------------------------------------------------------------------

    def get_batches_analytics(
        self,
        date_from: datetime,
        date_to: datetime,
        stage_id: Optional[int] = None,
        plantation_id: Optional[int] = None,
        is_depleted: Optional[bool] = None,
    ) -> dict:
        filters = self._date_filters(Batch.created_at, date_from, date_to)
        if stage_id is not None:
            filters.append(Batch.stage_id == stage_id)
        if plantation_id is not None:
            filters.append(Batch.plantation_id == plantation_id)
        if is_depleted is not None:
            filters.append(Batch.is_depleted == is_depleted)

        # KPIs
        kpi = self.db.query(
            func.count(Batch.id).label("total"),
            func.coalesce(func.avg(
                case((Batch.cost_per_kg.isnot(None), Batch.cost_per_kg))
            ), 0).label("avg_cpk"),
            func.coalesce(func.sum(Batch.initial_weight_kg), 0).label("total_wt"),
            func.count(case((Batch.is_depleted == True, Batch.id))).label("depleted"),  # noqa: E712
        ).filter(*filters).first()

        kpis = {
            "total_batches": kpi.total or 0,
            "avg_cost_per_kg": float(kpi.avg_cpk or 0),
            "total_weight_kg": float(kpi.total_wt or 0),
            "depleted_count": kpi.depleted or 0,
        }

        # Avg cost by stage
        stage_rows = (
            self.db.query(
                BatchStage.name.label("stage_name"),
                func.avg(Batch.cost_per_kg).label("avg_cpk"),
                func.count(Batch.id).label("cnt"),
            )
            .join(Batch.stage)
            .filter(*filters, Batch.cost_per_kg.isnot(None))
            .group_by(BatchStage.name)
            .order_by(BatchStage.name)
            .all()
        )
        avg_cost_by_stage = [
            {"stage_name": r.stage_name, "avg_cost_per_kg": float(r.avg_cpk or 0), "batch_count": r.cnt}
            for r in stage_rows
        ]

        # Cost trend by month
        period_expr = func.to_char(Batch.created_at, 'YYYY-MM')
        trend_rows = (
            self.db.query(
                period_expr.label("period"),
                func.avg(Batch.cost_per_kg).label("avg_cpk"),
            )
            .filter(*filters, Batch.cost_per_kg.isnot(None))
            .group_by(period_expr)
            .order_by(period_expr)
            .all()
        )
        cost_trend = [
            {"period": r.period, "avg_cost_per_kg": float(r.avg_cpk or 0)}
            for r in trend_rows
        ]

        # Top 10 cost contributors with breakdown
        top_batches = (
            self.db.query(Batch)
            .filter(*filters, Batch.cost_per_kg.isnot(None))
            .order_by(Batch.cost_per_kg.desc())
            .limit(10)
            .all()
        )
        top_cost_contributors = []
        for b in top_batches:
            breakdown = self._batch_cost_breakdown(b.id)
            top_cost_contributors.append({
                "batch_code": b.batch_code,
                "cost_per_kg": float(b.cost_per_kg),
                "breakdown": breakdown,
            })

        return {
            "kpis": kpis,
            "avg_cost_by_stage": avg_cost_by_stage,
            "cost_trend": cost_trend,
            "top_cost_contributors": top_cost_contributors,
        }

    def _batch_cost_breakdown(self, batch_id: int) -> dict:
        """Compute cost breakdown for a batch via its transformation inputs."""
        # Find transformations that produced this batch
        t_output = (
            self.db.query(TransformationOutput)
            .filter(TransformationOutput.batch_id == batch_id)
            .first()
        )
        if not t_output:
            return {"input_cost": 0.0, "labor_cost": 0.0, "consumable_cost": 0.0, "vehicle_cost": 0.0}

        t_id = t_output.transformation_id

        # Labor cost
        labor = self.db.query(
            func.coalesce(func.sum(TransformationPersonnel.total_wages_payable), 0)
        ).filter(TransformationPersonnel.transformation_id == t_id).scalar()

        # Consumable cost
        consumable = self.db.query(
            func.coalesce(func.sum(ConsumableConsumption.total_cost), 0)
        ).filter(ConsumableConsumption.transformation_id == t_id).scalar()

        # Vehicle cost (hours_used * cost_per_hour is not available; use fuel_cost)
        vehicle = self.db.query(
            func.coalesce(func.sum(TransformationVehicle.fuel_cost), 0)
        ).filter(TransformationVehicle.transformation_id == t_id).scalar()

        # Input cost: sum of (input batch cost_per_kg * input_weight) for all inputs
        input_rows = (
            self.db.query(
                TransformationInput.input_weight,
                Batch.cost_per_kg,
            )
            .join(Batch, TransformationInput.batch_id == Batch.id)
            .filter(TransformationInput.transformation_id == t_id)
            .all()
        )
        input_cost = sum(
            float(r.input_weight) * float(r.cost_per_kg)
            for r in input_rows
            if r.cost_per_kg is not None
        )

        return {
            "input_cost": float(input_cost),
            "labor_cost": float(labor),
            "consumable_cost": float(consumable),
            "vehicle_cost": float(vehicle),
        }

    # -----------------------------------------------------------------------
    # Transformations Analytics
    # -----------------------------------------------------------------------

    def get_transformations_analytics(
        self,
        date_from: datetime,
        date_to: datetime,
        type_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> dict:
        filters = self._date_filters(Transformation.from_date, date_from, date_to)
        if type_id is not None:
            filters.append(Transformation.type_id == type_id)
        if status == "active":
            filters.append(Transformation.to_date.is_(None))
        elif status == "completed":
            filters.append(Transformation.to_date.isnot(None))

        # --- KPIs ---
        # Total count
        total_count = self.db.query(func.count(Transformation.id)).filter(*filters).scalar() or 0

        # Avg completion days (completed only)
        completed_filters = filters + [Transformation.to_date.isnot(None)]
        avg_days_row = self.db.query(
            func.avg(
                func.extract('epoch', Transformation.to_date - Transformation.from_date) / 86400.0
            )
        ).filter(*completed_filters).scalar()
        avg_completion_days = float(avg_days_row) if avg_days_row else 0.0

        # Total cost: sum wages + consumables + vehicle fuel per transformation
        # Subquery approach: get transformation IDs in range, then sum costs
        t_ids_sq = (
            self.db.query(Transformation.id)
            .filter(*filters)
            .subquery()
        )

        total_labor = self.db.query(
            func.coalesce(func.sum(TransformationPersonnel.total_wages_payable), 0)
        ).filter(TransformationPersonnel.transformation_id.in_(
            self.db.query(t_ids_sq.c.id)
        )).scalar() or D("0")

        total_consumable = self.db.query(
            func.coalesce(func.sum(ConsumableConsumption.total_cost), 0)
        ).filter(ConsumableConsumption.transformation_id.in_(
            self.db.query(t_ids_sq.c.id)
        )).scalar() or D("0")

        total_vehicle = self.db.query(
            func.coalesce(func.sum(TransformationVehicle.fuel_cost), 0)
        ).filter(TransformationVehicle.transformation_id.in_(
            self.db.query(t_ids_sq.c.id)
        )).scalar() or D("0")

        total_cost = total_labor + total_consumable + total_vehicle
        avg_cost = total_cost / total_count if total_count > 0 else D("0")

        kpis = {
            "total_transformations": total_count,
            "avg_completion_days": avg_completion_days,
            "total_cost": total_cost,
            "avg_cost": avg_cost,
        }

        # --- Avg completion by type ---
        completion_rows = (
            self.db.query(
                TransformationType.name.label("type_name"),
                func.avg(
                    func.extract('epoch', Transformation.to_date - Transformation.from_date) / 86400.0
                ).label("avg_days"),
                func.count(Transformation.id).label("cnt"),
            )
            .join(Transformation.transformation_type)
            .filter(*completed_filters)
            .group_by(TransformationType.name)
            .order_by(TransformationType.name)
            .all()
        )
        avg_completion_by_type = [
            {"type_name": r.type_name, "avg_days": float(r.avg_days or 0), "count": r.cnt}
            for r in completion_rows
        ]

        # --- Avg cost by type ---
        # Per type: avg labor cost, avg consumable cost
        cost_type_rows = (
            self.db.query(
                TransformationType.name.label("type_name"),
                Transformation.id.label("t_id"),
            )
            .join(Transformation.transformation_type)
            .filter(*filters)
            .all()
        )
        # Group transformation IDs by type
        type_t_ids: dict[str, list[int]] = defaultdict(list)
        for r in cost_type_rows:
            type_t_ids[r.type_name].append(r.t_id)

        avg_cost_by_type = []
        for type_name in sorted(type_t_ids.keys()):
            t_id_list = type_t_ids[type_name]
            n = len(t_id_list)
            if n == 0:
                continue

            labor_sum = self.db.query(
                func.coalesce(func.sum(TransformationPersonnel.total_wages_payable), 0)
            ).filter(TransformationPersonnel.transformation_id.in_(t_id_list)).scalar() or D("0")

            cons_sum = self.db.query(
                func.coalesce(func.sum(ConsumableConsumption.total_cost), 0)
            ).filter(ConsumableConsumption.transformation_id.in_(t_id_list)).scalar() or D("0")

            avg_labor = labor_sum / n
            avg_cons = cons_sum / n
            avg_total = avg_labor + avg_cons

            avg_cost_by_type.append({
                "type_name": type_name,
                "avg_labor_cost": avg_labor,
                "avg_consumable_cost": avg_cons,
                "avg_total": avg_total,
            })

        # --- Resource utilization ---
        resource_utilization = []
        for type_name in sorted(type_t_ids.keys()):
            t_id_list = type_t_ids[type_name]
            n = len(t_id_list)
            if n == 0:
                continue

            personnel_count = self.db.query(
                func.count(TransformationPersonnel.id)
            ).filter(TransformationPersonnel.transformation_id.in_(t_id_list)).scalar() or 0

            vehicle_hours = self.db.query(
                func.coalesce(func.sum(TransformationVehicle.hours_used), 0)
            ).filter(TransformationVehicle.transformation_id.in_(t_id_list)).scalar() or D("0")

            resource_utilization.append({
                "type_name": type_name,
                "avg_personnel_count": float(personnel_count) / n,
                "avg_vehicle_hours": float(vehicle_hours) / n,
            })

        # --- Consumable usage by type ---
        consumable_usage_rows = (
            self.db.query(
                TransformationType.name.label("type_name"),
                Consumable.name.label("consumable_name"),
                func.avg(ConsumableConsumption.quantity_used).label("avg_qty"),
                func.avg(ConsumableConsumption.total_cost).label("avg_cost"),
            )
            .join(ConsumableConsumption.transformation)
            .join(Transformation.transformation_type)
            .join(ConsumableConsumption.consumable)
            .filter(*filters)
            .group_by(TransformationType.name, Consumable.name)
            .order_by(TransformationType.name, Consumable.name)
            .all()
        )
        consumable_usage_by_type = [
            {
                "type_name": r.type_name,
                "consumable_name": r.consumable_name,
                "avg_quantity": float(r.avg_qty or 0),
                "avg_cost": r.avg_cost or D("0"),
            }
            for r in consumable_usage_rows
        ]

        return {
            "kpis": kpis,
            "avg_completion_by_type": avg_completion_by_type,
            "avg_cost_by_type": avg_cost_by_type,
            "resource_utilization": resource_utilization,
            "consumable_usage_by_type": consumable_usage_by_type,
        }

    # -----------------------------------------------------------------------
    # Personnel Analytics
    # -----------------------------------------------------------------------

    def get_personnel_analytics(
        self,
        date_from: datetime,
        date_to: datetime,
        personnel_id: Optional[int] = None,
        type_id: Optional[int] = None,
    ) -> dict:
        # Only transformations where type measures_personnel_efficiency = True
        base_filters = self._date_filters(Transformation.from_date, date_from, date_to) + [
            TransformationType.measures_personnel_efficiency == True,  # noqa: E712
        ]
        if type_id is not None:
            base_filters.append(Transformation.type_id == type_id)

        tp_filters = list(base_filters)
        if personnel_id is not None:
            tp_filters.append(TransformationPersonnel.personnel_id == personnel_id)

        # KPIs
        kpi = (
            self.db.query(
                func.coalesce(func.sum(TransformationPersonnel.total_wages_payable), 0).label("total_wages"),
                func.count(TransformationPersonnel.id).label("assignment_count"),
                func.coalesce(func.sum(TransformationPersonnel.output_weight_considered), 0).label("total_output"),
                func.count(distinct(TransformationPersonnel.personnel_id)).label("active_count"),
            )
            .join(TransformationPersonnel.transformation)
            .join(Transformation.transformation_type)
            .filter(*tp_filters)
            .first()
        )

        total_wages = kpi.total_wages or D("0")
        assignment_count = kpi.assignment_count or 0
        avg_wage = total_wages / assignment_count if assignment_count > 0 else D("0")

        kpis = {
            "total_wages_paid": total_wages,
            "avg_wage_per_transformation": avg_wage,
            "total_output_kg": float(kpi.total_output or 0),
            "active_personnel_count": kpi.active_count or 0,
        }

        # Efficiency ranking: per personnel
        eff_rows = (
            self.db.query(
                Personnel.id.label("pid"),
                Personnel.name.label("pname"),
                func.coalesce(func.sum(TransformationPersonnel.total_wages_payable), 0).label("wages"),
                func.coalesce(func.sum(TransformationPersonnel.output_weight_considered), 0).label("output"),
                func.count(distinct(TransformationPersonnel.transformation_id)).label("t_count"),
            )
            .join(TransformationPersonnel.personnel)
            .join(TransformationPersonnel.transformation)
            .join(Transformation.transformation_type)
            .filter(*tp_filters)
            .group_by(Personnel.id, Personnel.name)
            .all()
        )
        efficiency_ranking = []
        for r in eff_rows:
            output_kg = float(r.output or 0)
            wages = r.wages or D("0")
            cpk = float(wages) / output_kg if output_kg > 0 else 0.0
            efficiency_ranking.append({
                "personnel_id": r.pid,
                "personnel_name": r.pname,
                "total_wages": wages,
                "total_output_kg": output_kg,
                "cost_per_kg": cpk,
                "transformation_count": r.t_count,
            })
        efficiency_ranking.sort(key=lambda x: x["cost_per_kg"])

        # Payment/output trend by month
        period_expr = func.to_char(Transformation.from_date, 'YYYY-MM')
        trend_rows = (
            self.db.query(
                period_expr.label("period"),
                func.coalesce(func.sum(TransformationPersonnel.total_wages_payable), 0).label("wages"),
                func.coalesce(func.sum(TransformationPersonnel.output_weight_considered), 0).label("output"),
            )
            .join(TransformationPersonnel.transformation)
            .join(Transformation.transformation_type)
            .filter(*tp_filters)
            .group_by(period_expr)
            .order_by(period_expr)
            .all()
        )
        payment_output_trend = []
        for r in trend_rows:
            output_kg = float(r.output or 0)
            wages = r.wages or D("0")
            cpk = float(wages) / output_kg if output_kg > 0 else 0.0
            payment_output_trend.append({
                "period": r.period,
                "total_wages": wages,
                "total_output_kg": output_kg,
                "cost_per_kg": cpk,
            })

        return {
            "kpis": kpis,
            "efficiency_ranking": efficiency_ranking,
            "payment_output_trend": payment_output_trend,
        }

    # -----------------------------------------------------------------------
    # Consumables Analytics
    # -----------------------------------------------------------------------

    def get_consumables_analytics(
        self,
        date_from: datetime,
        date_to: datetime,
        category_id: Optional[int] = None,
        consumable_id: Optional[int] = None,
    ) -> dict:
        # Consumption filters
        cons_filters = self._date_filters(ConsumableConsumption.consumption_date, date_from, date_to)
        if consumable_id is not None:
            cons_filters.append(ConsumableConsumption.consumable_id == consumable_id)

        # Purchase filters
        purch_filters = self._date_filters(ConsumablePurchase.purchase_date, date_from, date_to)
        if consumable_id is not None:
            purch_filters.append(ConsumablePurchase.consumable_id == consumable_id)

        # Apply category filter if provided
        if category_id is not None:
            cons_filters.append(Consumable.category_id == category_id)
            purch_filters.append(Consumable.category_id == category_id)

        # KPIs - total spend
        spend_q = self.db.query(
            func.coalesce(func.sum(ConsumableConsumption.total_cost), 0).label("total_spend"),
            func.count(distinct(ConsumableConsumption.consumable_id)).label("item_count"),
        ).filter(*cons_filters)
        if category_id is not None:
            spend_q = spend_q.join(ConsumableConsumption.consumable)
        kpi_spend = spend_q.first()

        total_spend = kpi_spend.total_spend or D("0")
        total_items = kpi_spend.item_count or 0

        # Top category by spend (respects all active filters)
        top_cat_row = (
            self.db.query(
                ConsumableCategory.name,
                func.sum(ConsumableConsumption.total_cost).label("cat_spend"),
            )
            .join(ConsumableConsumption.consumable)
            .join(Consumable.category)
            .filter(*cons_filters)
            .group_by(ConsumableCategory.name)
            .order_by(func.sum(ConsumableConsumption.total_cost).desc())
            .first()
        )
        top_category = top_cat_row.name if top_cat_row else None

        # Utilization by item
        # Purchased qty per consumable in date range
        purchased_map: dict[int, float] = {}
        purch_rows = (
            self.db.query(
                ConsumablePurchase.consumable_id,
                func.sum(ConsumablePurchase.quantity).label("pqty"),
            )
            .filter(*purch_filters)
        )
        if category_id is not None:
            purch_rows = purch_rows.join(ConsumablePurchase.consumable)
        purch_rows = purch_rows.group_by(ConsumablePurchase.consumable_id).all()
        for r in purch_rows:
            purchased_map[r.consumable_id] = float(r.pqty or 0)

        # Consumed qty per consumable in date range
        consumed_map: dict[int, float] = {}
        cons_rows = (
            self.db.query(
                ConsumableConsumption.consumable_id,
                func.sum(ConsumableConsumption.quantity_used).label("cqty"),
            )
            .filter(*cons_filters)
        )
        if category_id is not None:
            cons_rows = cons_rows.join(ConsumableConsumption.consumable)
        cons_rows = cons_rows.group_by(ConsumableConsumption.consumable_id).all()
        for r in cons_rows:
            consumed_map[r.consumable_id] = float(r.cqty or 0)

        all_consumable_ids = set(purchased_map.keys()) | set(consumed_map.keys())
        # Fetch names
        name_map: dict[int, str] = {}
        if all_consumable_ids:
            name_rows = (
                self.db.query(Consumable.id, Consumable.name)
                .filter(Consumable.id.in_(all_consumable_ids))
                .all()
            )
            for r in name_rows:
                name_map[r.id] = r.name

        utilization_by_item = []
        total_util_rate = 0.0
        util_count = 0
        for cid in sorted(all_consumable_ids):
            purchased = purchased_map.get(cid, 0.0)
            consumed = consumed_map.get(cid, 0.0)
            if purchased > 0:
                rate = min(consumed / purchased, 1.0)
            else:
                rate = 0.0
            total_util_rate += rate
            util_count += 1
            utilization_by_item.append({
                "consumable_id": cid,
                "consumable_name": name_map.get(cid, ""),
                "purchased_qty": purchased,
                "consumed_qty": consumed,
                "utilization_rate": round(rate, 4),
            })

        avg_utilization_rate = total_util_rate / util_count if util_count > 0 else 0.0

        kpis = {
            "total_spend": total_spend,
            "total_items": total_items,
            "top_category": top_category,
            "avg_utilization_rate": round(avg_utilization_rate, 4),
        }

        # Category cost spread
        cat_rows = (
            self.db.query(
                ConsumableCategory.name.label("cat_name"),
                Consumable.name.label("cons_name"),
                func.sum(ConsumableConsumption.total_cost).label("cost"),
            )
            .join(ConsumableConsumption.consumable)
            .join(Consumable.category)
            .filter(*cons_filters)
            .group_by(ConsumableCategory.name, Consumable.name)
            .order_by(ConsumableCategory.name, Consumable.name)
            .all()
        )

        grand_total = float(total_spend) if float(total_spend) > 0 else 1.0
        cat_groups: dict[str, dict] = {}
        for r in cat_rows:
            if r.cat_name not in cat_groups:
                cat_groups[r.cat_name] = {"total_cost": D("0"), "items": []}
            cat_groups[r.cat_name]["total_cost"] += r.cost or D("0")
            cat_groups[r.cat_name]["items"].append({
                "consumable_name": r.cons_name,
                "cost": r.cost or D("0"),
            })

        category_cost_spread = []
        for cat_name in sorted(cat_groups.keys()):
            grp = cat_groups[cat_name]
            pct = float(grp["total_cost"]) / grand_total * 100 if grand_total > 0 else 0.0
            category_cost_spread.append({
                "category_name": cat_name,
                "total_cost": grp["total_cost"],
                "percentage": round(pct, 2),
                "items": grp["items"],
            })

        # Spend over time
        period_expr = func.to_char(ConsumableConsumption.consumption_date, 'YYYY-MM')
        spend_time_q = (
            self.db.query(
                period_expr.label("period"),
                func.coalesce(func.sum(ConsumableConsumption.total_cost), 0).label("total_cost"),
            )
            .filter(*cons_filters)
        )
        if category_id is not None:
            spend_time_q = spend_time_q.join(ConsumableConsumption.consumable)
        spend_time_rows = (
            spend_time_q
            .group_by(period_expr)
            .order_by(period_expr)
            .all()
        )
        spend_over_time = [
            {"period": r.period, "total_cost": r.total_cost or D("0")}
            for r in spend_time_rows
        ]

        return {
            "kpis": kpis,
            "utilization_by_item": utilization_by_item,
            "category_cost_spread": category_cost_spread,
            "spend_over_time": spend_over_time,
        }

    # -----------------------------------------------------------------------
    # Expenses Analytics
    # -----------------------------------------------------------------------

    def get_expenses_analytics(
        self,
        date_from: datetime,
        date_to: datetime,
        category_id: Optional[int] = None,
        plantation_id: Optional[int] = None,
    ) -> dict:
        filters = self._date_filters(Expense.date, date_from, date_to)
        if category_id is not None:
            filters.append(Expense.category_id == category_id)
        if plantation_id is not None:
            filters.append(Expense.plantation_id == plantation_id)

        # KPIs
        kpi = self.db.query(
            func.coalesce(func.sum(Expense.amount), 0).label("total"),
            func.count(Expense.id).label("cnt"),
        ).filter(*filters).first()

        total_expenses = kpi.total or D("0")
        expense_count = kpi.cnt or 0

        # Months in range
        if date_from and date_to:
            delta_days = (date_to - date_from).days
            months = max(delta_days / 30.0, 1.0)
        else:
            months = 1.0
        avg_per_period = total_expenses / D(str(round(months))) if months > 0 else D("0")

        # Largest category
        largest_cat_row = (
            self.db.query(
                ExpenseCategory.name,
                func.sum(Expense.amount).label("cat_total"),
            )
            .join(Expense.category)
            .filter(*filters)
            .group_by(ExpenseCategory.name)
            .order_by(func.sum(Expense.amount).desc())
            .first()
        )
        largest_category = largest_cat_row.name if largest_cat_row else None

        kpis = {
            "total_expenses": total_expenses,
            "avg_per_period": avg_per_period,
            "largest_category": largest_category,
            "expense_count": expense_count,
        }

        # Category distribution
        cat_rows = (
            self.db.query(
                ExpenseCategory.name.label("cat_name"),
                func.sum(Expense.amount).label("total"),
                func.count(Expense.id).label("cnt"),
            )
            .join(Expense.category)
            .filter(*filters)
            .group_by(ExpenseCategory.name)
            .order_by(func.sum(Expense.amount).desc())
            .all()
        )
        grand_total = float(total_expenses) if float(total_expenses) > 0 else 1.0
        category_distribution = [
            {
                "category_name": r.cat_name,
                "total": r.total or D("0"),
                "percentage": round(float(r.total or 0) / grand_total * 100, 2),
                "count": r.cnt,
            }
            for r in cat_rows
        ]

        # Time distribution
        period_expr = func.to_char(Expense.date, 'YYYY-MM')
        time_rows = (
            self.db.query(
                period_expr.label("period"),
                func.coalesce(func.sum(Expense.amount), 0).label("total"),
                func.count(Expense.id).label("cnt"),
            )
            .filter(*filters)
            .group_by(period_expr)
            .order_by(period_expr)
            .all()
        )
        time_distribution = [
            {"period": r.period, "total": r.total or D("0"), "count": r.cnt}
            for r in time_rows
        ]

        return {
            "kpis": kpis,
            "category_distribution": category_distribution,
            "time_distribution": time_distribution,
        }

    # -----------------------------------------------------------------------
    # Plantations Analytics
    # -----------------------------------------------------------------------

    def get_plantations_analytics(
        self,
        date_from: datetime,
        date_to: datetime,
        plantation_id: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> dict:
        today = date.today()

        # Get all plantations with their leases
        p_query = self.db.query(Plantation).options(joinedload(Plantation.lease))
        if plantation_id is not None:
            p_query = p_query.filter(Plantation.id == plantation_id)
        plantations = p_query.all()

        if is_active is not None:
            plantations = [p for p in plantations if p.is_active == is_active]

        plantation_ids = [p.id for p in plantations]

        # Find HARVEST stage
        harvest_stage = (
            self.db.query(BatchStage)
            .filter(BatchStage.name.ilike('HARVEST%'))
            .first()
        )
        harvest_stage_id = harvest_stage.id if harvest_stage else -1

        # KPIs
        total_plantations = len(plantations)
        active_count = sum(1 for p in plantations if p.is_active)

        # Total harvest kg in date range
        harvest_wt = D("0")
        if plantation_ids:
            harvest_wt_row = self.db.query(
                func.coalesce(func.sum(Batch.initial_weight_kg), 0)
            ).filter(
                Batch.plantation_id.in_(plantation_ids),
                Batch.stage_id == harvest_stage_id,
                *self._date_filters(Batch.created_at, date_from, date_to),
            ).scalar() or D("0")
            harvest_wt = harvest_wt_row

        # Total lease cost in date range
        total_lease = D("0")
        if plantation_ids:
            lease_filters = [PlantationLease.plantation_id.in_(plantation_ids)]
            if date_from is not None and date_to is not None:
                lease_filters.append(or_(
                    and_(PlantationLease.start_date >= date_from, PlantationLease.start_date <= date_to),
                    and_(PlantationLease.end_date >= date_from, PlantationLease.end_date <= date_to),
                    and_(PlantationLease.start_date <= date_from,
                         or_(PlantationLease.end_date >= date_to, PlantationLease.end_date.is_(None))),
                ))
            total_lease_row = self.db.query(
                func.coalesce(func.sum(PlantationLease.cost), 0)
            ).filter(*lease_filters).scalar() or D("0")
            total_lease = total_lease_row

        kpis = {
            "total_plantations": total_plantations,
            "active_count": active_count,
            "total_harvest_kg": float(harvest_wt),
            "total_lease_cost": total_lease,
        }

        # Output over time: per (YYYY-MM, plantation), sum harvest batch weight
        output_over_time = []
        if plantation_ids:
            period_expr = func.to_char(Batch.created_at, 'YYYY-MM')
            output_rows = (
                self.db.query(
                    period_expr.label("period"),
                    Plantation.name.label("pname"),
                    func.coalesce(func.sum(Batch.initial_weight_kg), 0).label("wt"),
                )
                .join(Batch.plantation)
                .filter(
                    Batch.plantation_id.in_(plantation_ids),
                    Batch.stage_id == harvest_stage_id,
                    *self._date_filters(Batch.created_at, date_from, date_to),
                )
                .group_by(period_expr, Plantation.name)
                .order_by(period_expr, Plantation.name)
                .all()
            )
            output_over_time = [
                {"period": r.period, "plantation_name": r.pname, "harvest_kg": float(r.wt or 0)}
                for r in output_rows
            ]

        # Lease cost trends: only for plantations with long lease history
        lease_cost_trends = []
        p_name_map = {p.id: p.name for p in plantations}
        for p in plantations:
            leases = p.lease
            if not leases:
                continue
            # Check if long history: >=2 leases or single lease > 365 days
            has_long = len(leases) >= 2
            if not has_long and len(leases) == 1:
                l = leases[0]
                if l.end_date and l.start_date:
                    duration = (l.end_date - l.start_date).days
                    has_long = duration > 365
                elif l.end_date is None:
                    # Open-ended lease - consider it long
                    has_long = True
            if not has_long:
                continue

            # Per year, sum lease cost
            year_costs: dict[str, D] = defaultdict(lambda: D("0"))
            for l in leases:
                start_year = l.start_date.year
                end_year = l.end_date.year if l.end_date else today.year
                # Simple approach: assign full cost to start year
                # For multi-year leases, prorate
                if start_year == end_year:
                    year_costs[str(start_year)] += l.cost
                else:
                    total_days = (l.end_date - l.start_date).days if l.end_date else 365
                    if total_days <= 0:
                        total_days = 1
                    for yr in range(start_year, end_year + 1):
                        yr_start = max(l.start_date, datetime(yr, 1, 1))
                        yr_end_dt = l.end_date if l.end_date else datetime(today.year, 12, 31)
                        yr_end = min(yr_end_dt, datetime(yr, 12, 31))
                        days_in_yr = max((yr_end - yr_start).days, 0)
                        prorated = l.cost * D(str(days_in_yr)) / D(str(total_days))
                        year_costs[str(yr)] += prorated

            periods = [
                {"period": yr, "lease_cost": year_costs[yr]}
                for yr in sorted(year_costs.keys())
            ]
            lease_cost_trends.append({
                "plantation_name": p.name,
                "has_long_lease": True,
                "periods": periods,
            })

        # Lease to output ratio: per plantation in date range
        lease_to_output_ratio = []
        if plantation_ids:
            for p in plantations:
                # Annual lease cost for this plantation in date range
                p_lease_filters = [PlantationLease.plantation_id == p.id]
                if date_from is not None and date_to is not None:
                    p_lease_filters.append(or_(
                        and_(PlantationLease.start_date >= date_from, PlantationLease.start_date <= date_to),
                        and_(PlantationLease.end_date >= date_from, PlantationLease.end_date <= date_to),
                        and_(PlantationLease.start_date <= date_from,
                             or_(PlantationLease.end_date >= date_to, PlantationLease.end_date.is_(None))),
                    ))
                p_lease = self.db.query(
                    func.coalesce(func.sum(PlantationLease.cost), 0)
                ).filter(*p_lease_filters).scalar() or D("0")

                # Harvest kg for this plantation in date range
                p_harvest = self.db.query(
                    func.coalesce(func.sum(Batch.initial_weight_kg), 0)
                ).filter(
                    Batch.plantation_id == p.id,
                    Batch.stage_id == harvest_stage_id,
                    *self._date_filters(Batch.created_at, date_from, date_to),
                ).scalar() or D("0")

                p_harvest_f = float(p_harvest)
                cpk = float(p_lease) / p_harvest_f if p_harvest_f > 0 else 0.0

                if float(p_lease) > 0 or p_harvest_f > 0:
                    lease_to_output_ratio.append({
                        "plantation_name": p.name,
                        "annual_lease_cost": p_lease,
                        "annual_harvest_kg": p_harvest_f,
                        "cost_per_kg": round(cpk, 4),
                    })

        # Lease to revenue ratio: per plantation, annual revenue from sales
        # traced back to plantation's batches
        lease_to_revenue_ratio = []
        if plantation_ids:
            for p in plantations:
                # Get lease cost (reuse from above loop data if possible)
                p_lease_filters = [PlantationLease.plantation_id == p.id]
                if date_from is not None and date_to is not None:
                    p_lease_filters.append(or_(
                        and_(PlantationLease.start_date >= date_from, PlantationLease.start_date <= date_to),
                        and_(PlantationLease.end_date >= date_from, PlantationLease.end_date <= date_to),
                        and_(PlantationLease.start_date <= date_from,
                             or_(PlantationLease.end_date >= date_to, PlantationLease.end_date.is_(None))),
                    ))
                p_lease = self.db.query(
                    func.coalesce(func.sum(PlantationLease.cost), 0)
                ).filter(*p_lease_filters).scalar() or D("0")

                if float(p_lease) == 0:
                    continue

                # Find all batches from this plantation
                root_batch_ids = [
                    b_id for (b_id,) in
                    self.db.query(Batch.id).filter(Batch.plantation_id == p.id).all()
                ]
                if not root_batch_ids:
                    continue

                # Trace descendants
                all_descendant_ids = self._get_all_descendant_batch_ids(root_batch_ids)
                all_batch_ids = set(root_batch_ids) | all_descendant_ids

                # Revenue from sales allocated to these batches in date range
                revenue = self.db.query(
                    func.coalesce(func.sum(
                        SaleAllocation.quantity_allocated *
                        (Sale.selling_price / Sale.quantity_sold)
                    ), 0)
                ).join(SaleAllocation.sale).filter(
                    SaleAllocation.batch_id.in_(all_batch_ids),
                    *self._date_filters(Sale.sale_date, date_from, date_to),
                    Sale.status == "COMPLETED",
                ).scalar() or D("0")

                ratio = float(p_lease) / float(revenue) if float(revenue) > 0 else 0.0
                lease_to_revenue_ratio.append({
                    "plantation_name": p.name,
                    "annual_lease_cost": p_lease,
                    "annual_revenue": revenue,
                    "ratio": round(ratio, 4),
                })

        return {
            "kpis": kpis,
            "output_over_time": output_over_time,
            "lease_cost_trends": lease_cost_trends,
            "lease_to_output_ratio": lease_to_output_ratio,
            "lease_to_revenue_ratio": lease_to_revenue_ratio,
        }

    # -----------------------------------------------------------------------
    # Sales Lease Impact
    # -----------------------------------------------------------------------

    def get_sales_lease_impact(
        self,
        date_from: datetime,
        date_to: datetime,
        stage_id: Optional[int] = None,
        customer_q: Optional[str] = None,
        status: Optional[str] = None,
    ) -> dict:
        """
        Trace sold batches back to source plantations via batch_parents DAG,
        then compute lease cost impact on sold goods.
        """
        # Get completed sales in date range with allocations
        sale_filters = self._date_filters(Sale.sale_date, date_from, date_to)
        if status:
            sale_filters.append(Sale.status == status)
        else:
            sale_filters.append(Sale.status == "COMPLETED")
        if stage_id is not None:
            sale_filters.append(Sale.stage_id == stage_id)

        sale_q = self.db.query(Sale).options(joinedload(Sale.allocations)).filter(*sale_filters)
        if customer_q:
            pattern = f"%{customer_q}%"
            sale_q = sale_q.join(Sale.customer).filter(
                or_(Customer.name.ilike(pattern), Customer.phone.ilike(pattern))
            )
        sales = sale_q.all()

        # For each sale allocation, trace batch -> root ancestor plantations
        # Accumulate: per plantation, how much sold quantity traces back to it
        plantation_sold_qty: dict[int, float] = defaultdict(float)
        total_revenue = D("0")
        total_cogs = D("0")

        for sale in sales:
            total_revenue += sale.selling_price
            total_cogs += sale.cost_of_goods_sold
            for alloc in sale.allocations:
                # Find root ancestors of this batch
                roots = self._get_root_ancestors(alloc.batch_id)
                if not roots:
                    continue
                # Weight-proportional apportionment
                total_root_weight = sum(r["weight"] for r in roots)
                if total_root_weight <= 0:
                    continue
                for root in roots:
                    proportion = root["weight"] / total_root_weight
                    plantation_sold_qty[root["plantation_id"]] += float(alloc.quantity_allocated) * proportion

        # Get plantation data: lease cost, total harvest kg
        lease_impact_items = []
        total_lease_impact = D("0")

        plantation_ids = list(plantation_sold_qty.keys())
        if plantation_ids:
            plantations = (
                self.db.query(Plantation)
                .filter(Plantation.id.in_(plantation_ids))
                .all()
            )
            p_name_map = {p.id: p.name for p in plantations}

            # Find HARVEST stage
            harvest_stage = (
                self.db.query(BatchStage)
                .filter(BatchStage.name.ilike('HARVEST%'))
                .first()
            )
            harvest_stage_id = harvest_stage.id if harvest_stage else -1

            for pid in plantation_ids:
                # Total lease cost (all time for this plantation)
                lease_cost = self.db.query(
                    func.coalesce(func.sum(PlantationLease.cost), 0)
                ).filter(PlantationLease.plantation_id == pid).scalar() or D("0")

                # Total harvest kg (all time)
                total_harvest = self.db.query(
                    func.coalesce(func.sum(Batch.initial_weight_kg), 0)
                ).filter(
                    Batch.plantation_id == pid,
                    Batch.stage_id == harvest_stage_id,
                ).scalar() or D("0")

                total_harvest_f = float(total_harvest)
                lease_cpk = float(lease_cost) / total_harvest_f if total_harvest_f > 0 else 0.0
                sold_from_plantation = plantation_sold_qty[pid]
                impact = D(str(round(lease_cpk * sold_from_plantation, 2)))
                total_lease_impact += impact

                lease_impact_items.append({
                    "plantation_id": pid,
                    "plantation_name": p_name_map.get(pid, ""),
                    "lease_cost": lease_cost,
                    "total_harvest_kg": total_harvest_f,
                    "lease_cost_per_kg": round(lease_cpk, 4),
                    "impact_on_sold_goods": impact,
                })

        # Compute adjusted profit
        total_profit = total_revenue - total_cogs
        lease_adjusted_profit = total_profit - total_lease_impact
        lease_adjusted_margin_pct = (
            float(lease_adjusted_profit) / float(total_revenue) * 100
            if float(total_revenue) > 0 else 0.0
        )

        return {
            "lease_cost_impact": lease_impact_items,
            "total_lease_impact": total_lease_impact,
            "lease_adjusted_profit": lease_adjusted_profit,
            "lease_adjusted_margin_pct": round(lease_adjusted_margin_pct, 2),
        }

    # -----------------------------------------------------------------------
    # DAG Traversal Helpers
    # -----------------------------------------------------------------------

    def _get_root_ancestors(self, batch_id: int) -> list[dict]:
        """
        Traverse batch_parents DAG upward to find root ancestor batches
        (those with plantation_id set). Returns list of
        {"plantation_id": int, "weight": float} for weight-proportional apportionment.
        """
        visited: set[int] = set()
        roots: list[dict] = []
        queue = [batch_id]

        while queue:
            current_id = queue.pop()
            if current_id in visited:
                continue
            visited.add(current_id)

            # Check if this batch is a root (has plantation_id)
            batch = self.db.query(
                Batch.id, Batch.plantation_id, Batch.initial_weight_kg
            ).filter(Batch.id == current_id).first()

            if not batch:
                continue

            if batch.plantation_id is not None:
                roots.append({
                    "plantation_id": batch.plantation_id,
                    "weight": float(batch.initial_weight_kg),
                })
            else:
                # Find parents
                parent_rows = (
                    self.db.query(BatchParent.parent_batch_id)
                    .filter(BatchParent.child_batch_id == current_id)
                    .all()
                )
                for (parent_id,) in parent_rows:
                    if parent_id not in visited:
                        queue.append(parent_id)

        return roots

    def _get_all_descendant_batch_ids(self, root_batch_ids: list[int]) -> set[int]:
        """
        Traverse batch_parents DAG downward to find all descendant batch IDs.
        """
        visited: set[int] = set()
        queue = list(root_batch_ids)

        while queue:
            current_id = queue.pop()
            if current_id in visited:
                continue
            visited.add(current_id)

            child_rows = (
                self.db.query(BatchParent.child_batch_id)
                .filter(BatchParent.parent_batch_id == current_id)
                .all()
            )
            for (child_id,) in child_rows:
                if child_id not in visited:
                    queue.append(child_id)

        # Remove the roots themselves from descendants
        return visited - set(root_batch_ids)
