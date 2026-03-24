from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List

from sqlalchemy import func
from sqlalchemy.orm import Session, aliased, joinedload

from ..models.batch import Batch, BatchStage
from ..models.transformation import Transformation, TransformationOutput
from ..schemas.dashboard import (
    DailyOutputItem,
    DailyStageOutput,
    DashboardSummary,
    RecentActivityItem,
    StageSummaryItem,
    YieldTrendItem,
)


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_summary(self) -> DashboardSummary:
        ParentStage = aliased(BatchStage)
        current_year_start = datetime(datetime.now(timezone.utc).year, 1, 1, tzinfo=timezone.utc)
        stage_rows = (
            self.db.query(
                BatchStage.id,
                BatchStage.name,
                BatchStage.icon,
                BatchStage.color,
                func.count(Batch.id).label("batch_count"),
                func.coalesce(func.sum(Batch.remaining_weight_kg), 0).label(
                    "total_remaining_kg"
                ),
            )
            .outerjoin(ParentStage, BatchStage.parent_id == ParentStage.id)
            .outerjoin(
                Batch,
                (Batch.stage_id == BatchStage.id)
                & (Batch.is_depleted == False)  # noqa: E712
                & (Batch.created_at >= current_year_start),
            )
            .filter(BatchStage.is_waste == False)  # noqa: E712
            .group_by(
                BatchStage.id, BatchStage.name, BatchStage.icon, BatchStage.color,
                BatchStage.sort_order, BatchStage.batch_stage_level,
                ParentStage.sort_order,
            )
            .order_by(
                func.coalesce(ParentStage.sort_order, BatchStage.sort_order),
                BatchStage.batch_stage_level,
                BatchStage.sort_order,
            )
            .all()
        )

        stages = [
            StageSummaryItem(
                stage_id=row.id,
                stage_name=row.name,
                icon=row.icon,
                color=row.color,
                batch_count=row.batch_count,
                total_remaining_kg=Decimal(str(row.total_remaining_kg)),
            )
            for row in stage_rows
        ]

        active_count = (
            self.db.query(func.count(Transformation.id))
            .filter(Transformation.to_date.is_(None))
            .scalar()
            or 0
        )

        total_kg = (
            self.db.query(func.coalesce(func.sum(Batch.remaining_weight_kg), 0))
            .join(BatchStage, Batch.stage_id == BatchStage.id)
            .filter(
                Batch.is_depleted == False,  # noqa: E712
                BatchStage.is_waste == False,  # noqa: E712
            )
            .scalar()
        )
        total_kg = Decimal(str(total_kg))

        # Avg yield rate last 30 days
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        recent = (
            self.db.query(Transformation)
            .options(
                joinedload(Transformation.inputs),
                joinedload(Transformation.outputs).joinedload(TransformationOutput.batch).joinedload(Batch.stage),
            )
            .filter(
                Transformation.to_date.isnot(None),
                Transformation.to_date >= thirty_days_ago,
            )
            .all()
        )

        avg_yield = None
        if recent:
            yields = []
            for t in recent:
                total_in = sum((i.input_weight for i in t.inputs), Decimal("0"))
                total_out = sum(
                    (o.output_weight for o in t.outputs
                     if not (o.batch and o.batch.stage and o.batch.stage.is_waste)),
                    Decimal("0")
                )
                if total_in > 0:
                    yields.append(total_out / total_in * 100)
            if yields:
                avg_yield = sum(yields) / len(yields)

        return DashboardSummary(
            stages=stages,
            active_transformation_count=active_count,
            total_kg_in_pipeline=total_kg,
            avg_yield_rate_30d=avg_yield,
        )

    def get_yield_trend(self, weeks: int = 8) -> List[YieldTrendItem]:
        results = []
        now = datetime.now(timezone.utc)
        for i in range(weeks - 1, -1, -1):
            week_start = now - timedelta(weeks=i + 1)
            week_end = now - timedelta(weeks=i)
            total = (
                self.db.query(
                    func.coalesce(func.sum(TransformationOutput.output_weight), 0)
                )
                .join(
                    Transformation,
                    Transformation.id == TransformationOutput.transformation_id,
                )
                .filter(
                    Transformation.to_date.isnot(None),
                    Transformation.to_date >= week_start,
                    Transformation.to_date < week_end,
                )
                .scalar()
            )
            iso_week = week_start.isocalendar()
            results.append(
                YieldTrendItem(
                    week_label=f"{iso_week.year}-W{iso_week.week:02d}",
                    total_output_kg=Decimal(str(total)),
                )
            )
        return results

    def get_daily_output(self, end_date=None) -> List[DailyOutputItem]:
        from datetime import date as date_type

        if end_date is None:
            end_date = date_type.today()

        results = []
        for i in range(6, -1, -1):  # 7 days: end_date-6 ... end_date
            day = end_date - timedelta(days=i)
            day_start = datetime(day.year, day.month, day.day, 0, 0, 0, tzinfo=timezone.utc)
            day_end = datetime(day.year, day.month, day.day, 23, 59, 59, 999999, tzinfo=timezone.utc)

            # Total output for the day
            total = (
                self.db.query(
                    func.coalesce(func.sum(TransformationOutput.output_weight), 0)
                )
                .join(Transformation, Transformation.id == TransformationOutput.transformation_id)
                .filter(
                    Transformation.to_date.isnot(None),
                    Transformation.to_date >= day_start,
                    Transformation.to_date <= day_end,
                )
                .scalar()
            )

            # Per-stage breakdown
            stage_rows = (
                self.db.query(
                    BatchStage.name,
                    BatchStage.color,
                    func.coalesce(func.sum(TransformationOutput.output_weight), 0).label("output_kg"),
                )
                .join(Batch, Batch.id == TransformationOutput.batch_id)
                .join(BatchStage, BatchStage.id == Batch.stage_id)
                .join(Transformation, Transformation.id == TransformationOutput.transformation_id)
                .filter(
                    Transformation.to_date.isnot(None),
                    Transformation.to_date >= day_start,
                    Transformation.to_date <= day_end,
                )
                .group_by(BatchStage.name, BatchStage.color)
                .all()
            )

            stages = [
                DailyStageOutput(
                    stage_name=row.name,
                    stage_color=row.color,
                    output_kg=float(Decimal(str(row.output_kg))),
                )
                for row in stage_rows
                if float(Decimal(str(row.output_kg))) > 0
            ]

            results.append(
                DailyOutputItem(
                    date_label=day_start.strftime("%b %d"),
                    total_output_kg=float(Decimal(str(total))),
                    stages=stages,
                )
            )
        return results

    def get_recent_activity(self, limit: int = 5) -> List[RecentActivityItem]:
        activities = []

        harvest_batches = (
            self.db.query(Batch)
            .join(BatchStage, Batch.stage_id == BatchStage.id)
            .filter(BatchStage.name.ilike("HARVEST%"))
            .order_by(Batch.created_at.desc())
            .limit(3)
            .all()
        )
        for b in harvest_batches:
            activities.append(
                RecentActivityItem(
                    event_type="harvest",
                    description=f"Harvest batch {b.batch_code} created ({b.initial_weight_kg} kg)",
                    date=b.created_at.isoformat(),
                    entity_id=b.id,
                    entity_type="batch",
                )
            )

        completed = (
            self.db.query(Transformation)
            .options(joinedload(Transformation.transformation_type))
            .filter(Transformation.to_date.isnot(None))
            .order_by(Transformation.to_date.desc())
            .limit(3)
            .all()
        )
        for t in completed:
            type_name = (
                t.transformation_type.name if t.transformation_type else "Processing"
            )
            activities.append(
                RecentActivityItem(
                    event_type="transformation_complete",
                    description=f"{type_name} transformation T-{t.id} completed",
                    date=t.to_date.isoformat(),
                    entity_id=t.id,
                    entity_type="transformation",
                )
            )

        activities.sort(key=lambda x: x.date, reverse=True)
        return activities[:limit]
