from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from ..models.batch import Batch, BatchStage
from ..models.transformation import Transformation, TransformationOutput
from ..schemas.dashboard import (
    DailyOutputItem,
    DashboardSummary,
    RecentActivityItem,
    StageSummaryItem,
    YieldTrendItem,
)


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_summary(self) -> DashboardSummary:
        stage_rows = (
            self.db.query(
                BatchStage.id,
                BatchStage.name,
                func.count(Batch.id).label("batch_count"),
                func.coalesce(func.sum(Batch.remaining_weight_kg), 0).label(
                    "total_remaining_kg"
                ),
            )
            .outerjoin(Batch, Batch.stage_id == BatchStage.id)
            .group_by(BatchStage.id, BatchStage.name)
            .order_by(BatchStage.batch_stage_level)
            .all()
        )

        stages = [
            StageSummaryItem(
                stage_id=row.id,
                stage_name=row.name,
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
            .filter(Batch.is_depleted == False)  # noqa: E712
            .scalar()
        )
        total_kg = Decimal(str(total_kg))

        # Avg yield rate last 30 days
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        recent = (
            self.db.query(Transformation)
            .options(
                joinedload(Transformation.inputs),
                joinedload(Transformation.outputs),
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
                total_out = sum((o.output_weight for o in t.outputs), Decimal("0"))
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

    def get_daily_output(self, days: int = 7) -> List[DailyOutputItem]:
        results = []
        now = datetime.now(timezone.utc)
        for i in range(days - 1, -1, -1):
            day_start = (now - timedelta(days=i + 1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            day_end = (now - timedelta(days=i)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
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
                    Transformation.to_date >= day_start,
                    Transformation.to_date < day_end,
                )
                .scalar()
            )
            results.append(
                DailyOutputItem(
                    date_label=day_start.strftime("%b %d"),
                    total_output_kg=float(Decimal(str(total))),
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
