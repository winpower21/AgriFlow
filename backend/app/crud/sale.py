from datetime import datetime, timezone
from decimal import Decimal as D
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from ..models.batch import Batch, BatchStage
from ..models.customer import Customer
from ..models.sales import Sale, SaleAllocation
from ..schemas.sale import SaleCreate, SaleReject


class SaleService:
    def __init__(self, db: Session):
        self.db = db

    def get_list(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        stage_id: Optional[int] = None,
        customer_q: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Sale]:
        q = (
            self.db.query(Sale)
            .options(
                joinedload(Sale.customer),
                joinedload(Sale.stage),
            )
        )
        if date_from:
            q = q.filter(Sale.sale_date >= date_from)
        if date_to:
            q = q.filter(Sale.sale_date <= date_to)
        if stage_id:
            q = q.filter(Sale.stage_id == stage_id)
        if status:
            q = q.filter(Sale.status == status)
        if customer_q:
            pattern = f"%{customer_q}%"
            q = q.join(Sale.customer).filter(
                (Customer.name.ilike(pattern)) | (Customer.phone.ilike(pattern))
            )
        return q.order_by(Sale.sale_date.desc()).offset(skip).limit(limit).all()

    def get_by_id(self, sale_id: int) -> Optional[Sale]:
        return (
            self.db.query(Sale)
            .options(
                joinedload(Sale.customer),
                joinedload(Sale.stage),
                joinedload(Sale.allocations).joinedload(SaleAllocation.batch),
                joinedload(Sale.created_by),
                joinedload(Sale.reviewed_by),
                joinedload(Sale.paid_by),
            )
            .filter(Sale.id == sale_id)
            .first()
        )

    def get_salable_stages(self) -> list[BatchStage]:
        return (
            self.db.query(BatchStage)
            .filter(BatchStage.is_salable == True)
            .order_by(BatchStage.batch_stage_level.asc().nullslast())
            .all()
        )

    def get_salable_batches(self, stage_id: int) -> list[Batch]:
        """Get non-depleted batches at a salable stage with cost_per_kg set."""
        return (
            self.db.query(Batch)
            .filter(
                Batch.stage_id == stage_id,
                Batch.is_depleted == False,
                Batch.remaining_weight_kg > 0,
                Batch.cost_per_kg.isnot(None),
            )
            .order_by(Batch.created_at.asc())
            .all()
        )

    def create_sale(
        self, data: SaleCreate, user_id: int, is_admin: bool
    ) -> tuple[Optional[Sale], Optional[str]]:
        """Create a sale. Returns (sale, None) on success or (None, error_string) on failure."""

        # Validate allocation_mode
        if data.allocation_mode not in ("FIFO", "MANUAL"):
            return None, "allocation_mode must be FIFO or MANUAL"

        # Validate stage is salable
        stage = (
            self.db.query(BatchStage)
            .filter(BatchStage.id == data.stage_id, BatchStage.is_salable == True)
            .first()
        )
        if not stage:
            return None, "Stage not found or not salable"

        # Validate customer exists
        customer = self.db.query(Customer).filter(Customer.id == data.customer_id).first()
        if not customer:
            return None, "Customer not found"

        # Determine status
        sale_status = "COMPLETED" if is_admin else "PENDING"

        # Validate payment method required if marking as paid
        if data.is_paid and is_admin and not data.payment_method:
            return None, "payment_method is required when is_paid=True"

        # Create the sale record
        sale = Sale(
            sale_date=data.sale_date,
            quantity_sold=data.quantity_sold,
            selling_price=data.selling_price,
            cost_of_goods_sold=D("0"),  # Computed below
            customer_id=data.customer_id,
            stage_id=data.stage_id,
            status=sale_status,
            allocation_mode=data.allocation_mode,
            created_by_id=user_id,
            notes=data.notes,
            is_paid=data.is_paid if is_admin else False,
            payment_method=data.payment_method if (data.is_paid and is_admin) else None,
            paid_at=datetime.now(timezone.utc) if (data.is_paid and is_admin) else None,
            paid_by_id=user_id if (data.is_paid and is_admin) else None,
        )
        self.db.add(sale)
        self.db.flush()  # Get sale.id

        # Allocate
        if data.allocation_mode == "FIFO":
            error = self._allocate_fifo(sale, data.stage_id, data.quantity_sold)
        else:
            if not data.manual_allocations:
                return None, "manual_allocations required for MANUAL mode"
            error = self._allocate_manual(
                sale, data.stage_id, data.quantity_sold, data.manual_allocations
            )

        if error:
            self.db.rollback()
            return None, error

        # Auto-generate invoice number: dd-mm-yy-cust_id-first_batch_id-counter
        # Counter = total sales on that date (including this one)
        sale_date_start = data.sale_date.replace(hour=0, minute=0, second=0, microsecond=0)
        sale_date_end = sale_date_start.replace(hour=23, minute=59, second=59)
        day_sale_count = (
            self.db.query(func.count(Sale.id))
            .filter(Sale.sale_date >= sale_date_start, Sale.sale_date <= sale_date_end)
            .scalar()
        )
        first_batch_id = sale.allocations[0].batch_id if sale.allocations else 0
        date_part = data.sale_date.strftime("%d-%m-%y")
        sale.invoice_number = f"{date_part}-{data.customer_id}-{first_batch_id}-{day_sale_count}"

        self.db.commit()
        self.db.refresh(sale)
        return sale, None

    def _allocate_fifo(
        self, sale: Sale, stage_id: int, quantity: D
    ) -> Optional[str]:
        """FIFO allocation: oldest batches first. Returns error string or None."""
        # Lock rows for update to prevent race conditions
        batches = (
            self.db.query(Batch)
            .filter(
                Batch.stage_id == stage_id,
                Batch.is_depleted == False,
                Batch.remaining_weight_kg > 0,
                Batch.cost_per_kg.isnot(None),
            )
            .order_by(Batch.created_at.asc())
            .with_for_update()
            .all()
        )

        remaining = D(str(quantity))
        total_cogs = D("0")

        for batch in batches:
            if remaining <= 0:
                break
            alloc_qty = min(batch.remaining_weight_kg, remaining)
            alloc_cost = alloc_qty * batch.cost_per_kg

            alloc = SaleAllocation(
                sale_id=sale.id,
                batch_id=batch.id,
                quantity_allocated=alloc_qty,
                cost_allocated=alloc_cost,
            )
            self.db.add(alloc)

            batch.remaining_weight_kg -= alloc_qty
            if batch.remaining_weight_kg <= 0:
                batch.is_depleted = True

            remaining -= alloc_qty
            total_cogs += alloc_cost

        if remaining > 0:
            return f"Insufficient stock: {remaining}kg still unallocated"

        sale.cost_of_goods_sold = total_cogs
        return None

    def _allocate_manual(
        self, sale: Sale, stage_id: int, quantity: D, batch_selections: list
    ) -> Optional[str]:
        """Manual allocation: user-specified batch order. Returns error string or None."""
        batch_ids = [b.batch_id for b in batch_selections]

        # Lock selected batches
        batches_map = {}
        for bid in batch_ids:
            batch = (
                self.db.query(Batch)
                .filter(
                    Batch.id == bid,
                    Batch.stage_id == stage_id,
                    Batch.is_depleted == False,
                    Batch.remaining_weight_kg > 0,
                    Batch.cost_per_kg.isnot(None),
                )
                .with_for_update()
                .first()
            )
            if not batch:
                return f"Batch {bid} not found, depleted, or not at the correct stage"
            batches_map[bid] = batch

        # Validate: reject unnecessary batches upfront
        # If batch N can cover the remaining qty, batches N+1... are unnecessary
        check_remaining = D(str(quantity))
        needed_count = 0
        for bid in batch_ids:
            if check_remaining <= 0:
                break
            batch = batches_map[bid]
            check_remaining -= min(batch.remaining_weight_kg, check_remaining)
            needed_count += 1
        if needed_count < len(batch_ids):
            return f"Unnecessary batches provided — first {needed_count} batch(es) cover the full quantity"

        remaining = D(str(quantity))
        total_cogs = D("0")

        for bid in batch_ids:
            if remaining <= 0:
                break
            batch = batches_map[bid]
            alloc_qty = min(batch.remaining_weight_kg, remaining)
            alloc_cost = alloc_qty * batch.cost_per_kg

            alloc = SaleAllocation(
                sale_id=sale.id,
                batch_id=batch.id,
                quantity_allocated=alloc_qty,
                cost_allocated=alloc_cost,
            )
            self.db.add(alloc)

            batch.remaining_weight_kg -= alloc_qty
            if batch.remaining_weight_kg <= 0:
                batch.is_depleted = True

            remaining -= alloc_qty
            total_cogs += alloc_cost

        if remaining > 0:
            return f"Insufficient stock: {remaining}kg still unallocated"

        sale.cost_of_goods_sold = total_cogs
        return None

    def approve(self, sale_id: int, user_id: int) -> Optional[str]:
        """Approve a pending sale. Returns error string or None."""
        sale = self.db.query(Sale).filter(Sale.id == sale_id).first()
        if not sale:
            return "not_found"
        if sale.status != "PENDING":
            return "not_pending"

        sale.status = "COMPLETED"
        sale.reviewed_by_id = user_id
        sale.reviewed_at = datetime.now(timezone.utc)
        self.db.commit()
        return None

    def reject(self, sale_id: int, user_id: int, data: SaleReject) -> Optional[str]:
        """Reject a pending sale and reverse inventory reservation."""
        sale = (
            self.db.query(Sale)
            .options(joinedload(Sale.allocations))
            .filter(Sale.id == sale_id)
            .first()
        )
        if not sale:
            return "not_found"
        if sale.status != "PENDING":
            return "not_pending"

        # Reverse allocations — lock batches
        for alloc in sale.allocations:
            batch = (
                self.db.query(Batch)
                .filter(Batch.id == alloc.batch_id)
                .with_for_update()
                .first()
            )
            if batch:
                batch.remaining_weight_kg += alloc.quantity_allocated
                if batch.is_depleted:
                    batch.is_depleted = False

        # Delete allocations
        for alloc in list(sale.allocations):
            self.db.delete(alloc)

        sale.status = "REJECTED"
        sale.rejection_reason = data.rejection_reason
        sale.reviewed_by_id = user_id
        sale.reviewed_at = datetime.now(timezone.utc)
        self.db.commit()
        return None

    def delete(self, sale_id: int) -> Optional[str]:
        """Delete a sale. Reverses batch allocations for PENDING and COMPLETED."""
        sale = (
            self.db.query(Sale)
            .options(joinedload(Sale.allocations))
            .filter(Sale.id == sale_id)
            .first()
        )
        if not sale:
            return "not_found"

        # Reverse allocations if PENDING or COMPLETED (REJECTED already reversed)
        if sale.status in ("PENDING", "COMPLETED"):
            for alloc in sale.allocations:
                batch = (
                    self.db.query(Batch)
                    .filter(Batch.id == alloc.batch_id)
                    .with_for_update()
                    .first()
                )
                if batch:
                    batch.remaining_weight_kg += alloc.quantity_allocated
                    if batch.is_depleted:
                        batch.is_depleted = False

        self.db.delete(sale)
        self.db.commit()
        return None

    def mark_paid(self, sale_id: int, payment_method: str, user_id: int) -> Optional[str]:
        """Mark a completed credit sale as paid. Returns error string or None."""
        sale = self.db.query(Sale).filter(Sale.id == sale_id).first()
        if not sale:
            return "not_found"
        if sale.status != "COMPLETED":
            return "not_completed"
        if sale.is_paid:
            return "already_paid"

        sale.is_paid = True
        sale.payment_method = payment_method
        sale.paid_at = datetime.now(timezone.utc)
        sale.paid_by_id = user_id
        self.db.commit()
        return None

    def get_analytics(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        stage_id: Optional[int] = None,
        customer_q: Optional[str] = None,
        status: Optional[str] = None,
        is_admin: bool = False,
    ) -> dict:
        """Compute aggregated analytics for the dashboard."""
        pattern = f"%{customer_q}%" if customer_q else None

        # Determine granularity
        if date_from and date_to:
            delta = (date_to - date_from).days
            granularity = "month" if delta > 90 else "day"
        else:
            granularity = "month"

        if granularity == "day":
            period_expr = func.to_char(Sale.sale_date, 'YYYY-MM-DD')
        else:
            period_expr = func.to_char(Sale.sale_date, 'YYYY-MM')

        # Apply same filters to all sub-queries by building filter list
        filters = []
        if status:
            filters.append(Sale.status == status)
        else:
            filters.append(Sale.status == "COMPLETED")
        if date_from:
            filters.append(Sale.sale_date >= date_from)
        if date_to:
            filters.append(Sale.sale_date <= date_to)
        if stage_id:
            filters.append(Sale.stage_id == stage_id)

        # KPIs
        kpi_row = (
            self.db.query(
                func.count(Sale.id).label("cnt"),
                func.coalesce(func.sum(Sale.selling_price), 0).label("revenue"),
                func.coalesce(func.sum(Sale.quantity_sold), 0).label("volume"),
                func.coalesce(func.sum(Sale.cost_of_goods_sold), 0).label("cogs"),
            )
            .filter(*filters)
        )
        if customer_q:
            kpi_row = kpi_row.join(Sale.customer).filter(
                (Customer.name.ilike(pattern)) | (Customer.phone.ilike(pattern))
            )
        kpi = kpi_row.first()

        total_count = kpi.cnt or 0
        total_revenue = kpi.revenue or D("0")
        total_volume = kpi.volume or D("0")
        total_cogs = kpi.cogs or D("0")
        total_profit = total_revenue - total_cogs
        avg_sale = total_revenue / total_count if total_count > 0 else D("0")
        avg_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else D("0")

        # Payment breakdown
        payment_row = (
            self.db.query(
                Sale.is_paid,
                func.count(Sale.id).label("cnt"),
                func.coalesce(func.sum(Sale.selling_price), 0).label("amt"),
            )
            .filter(*filters)
        )
        if customer_q:
            payment_row = payment_row.join(Sale.customer).filter(
                (Customer.name.ilike(pattern)) | (Customer.phone.ilike(pattern))
            )
        payment_rows = payment_row.group_by(Sale.is_paid).all()

        paid_count = paid_amount = credit_count = credit_amount = 0
        for row in payment_rows:
            if row.is_paid:
                paid_count = row.cnt
                paid_amount = row.amt
            else:
                credit_count = row.cnt
                credit_amount = row.amt

        kpis = {
            "total_sales_count": total_count,
            "total_revenue": total_revenue,
            "total_volume_kg": total_volume,
            "avg_sale_value": avg_sale,
            "outstanding_credit_amount": credit_amount,
            "paid_amount": paid_amount,
            "total_profit": total_profit if is_admin else None,
            "avg_profit_margin": avg_margin if is_admin else None,
            "paid_count": paid_count,
            "credit_count": credit_count,
        }

        # Revenue/Volume over time
        time_q = (
            self.db.query(
                period_expr.label("period"),
                func.coalesce(func.sum(Sale.selling_price), 0).label("revenue"),
                func.coalesce(func.sum(Sale.quantity_sold), 0).label("volume"),
                func.count(Sale.id).label("cnt"),
            )
            .filter(*filters)
        )
        if customer_q:
            time_q = time_q.join(Sale.customer).filter(
                (Customer.name.ilike(pattern)) | (Customer.phone.ilike(pattern))
            )
        time_rows = time_q.group_by(period_expr).order_by(period_expr).all()

        time_series = [
            {"period": r.period, "revenue": r.revenue, "volume_kg": r.volume, "count": r.cnt}
            for r in time_rows
        ]
        revenue_over_time = time_series
        volume_over_time = time_series

        # Sales by stage
        stage_q = (
            self.db.query(
                BatchStage.name.label("stage_name"),
                func.coalesce(func.sum(Sale.selling_price), 0).label("revenue"),
                func.coalesce(func.sum(Sale.quantity_sold), 0).label("volume"),
                func.count(Sale.id).label("cnt"),
            )
            .join(Sale.stage)
            .filter(*filters)
        )
        if customer_q:
            stage_q = stage_q.join(Sale.customer).filter(
                (Customer.name.ilike(pattern)) | (Customer.phone.ilike(pattern))
            )
        stage_rows = stage_q.group_by(BatchStage.name).order_by(func.sum(Sale.selling_price).desc()).all()

        sales_by_stage = [
            {"stage_name": r.stage_name, "revenue": r.revenue, "volume_kg": r.volume, "count": r.cnt}
            for r in stage_rows
        ]

        # Top 5 customers
        cust_q = (
            self.db.query(
                Customer.id.label("customer_id"),
                Customer.name.label("customer_name"),
                func.coalesce(func.sum(Sale.selling_price), 0).label("revenue"),
                func.coalesce(func.sum(Sale.quantity_sold), 0).label("volume"),
            )
            .join(Sale.customer)
            .filter(*filters)
        )
        if customer_q:
            cust_q = cust_q.filter(
                (Customer.name.ilike(pattern)) | (Customer.phone.ilike(pattern))
            )
        cust_rows = (
            cust_q.group_by(Customer.id, Customer.name)
            .order_by(func.sum(Sale.selling_price).desc())
            .limit(5)
            .all()
        )

        top_customers = [
            {"customer_id": r.customer_id, "customer_name": r.customer_name, "revenue": r.revenue, "volume_kg": r.volume}
            for r in cust_rows
        ]

        # Profit over time (admin only)
        profit_over_time = []
        if is_admin:
            profit_q = (
                self.db.query(
                    period_expr.label("period"),
                    func.coalesce(func.sum(Sale.selling_price - Sale.cost_of_goods_sold), 0).label("profit"),
                    func.coalesce(func.sum(Sale.selling_price), 0).label("revenue"),
                )
                .filter(*filters)
            )
            if customer_q:
                profit_q = profit_q.join(Sale.customer).filter(
                    (Customer.name.ilike(pattern)) | (Customer.phone.ilike(pattern))
                )
            profit_rows = profit_q.group_by(period_expr).order_by(period_expr).all()

            profit_over_time = [
                {
                    "period": r.period,
                    "profit": r.profit,
                    "margin_pct": (r.profit / r.revenue * 100) if r.revenue and r.revenue > 0 else D("0"),
                }
                for r in profit_rows
            ]

        return {
            "granularity": granularity,
            "kpis": kpis,
            "revenue_over_time": revenue_over_time,
            "volume_over_time": volume_over_time,
            "sales_by_stage": sales_by_stage,
            "top_customers": top_customers,
            "payment_breakdown": {
                "paid_count": paid_count,
                "paid_amount": paid_amount,
                "credit_count": credit_count,
                "credit_amount": credit_amount,
            },
            "profit_over_time": profit_over_time,
        }
