"""
Personnel CRUD service module.

Provides ``PersonnelService``, which manages worker/staff records and
their associated wage types.

Key design notes:
  - **Eager loading of wage types**: Both ``get_all()`` and ``get_by_id()``
    use SQLAlchemy ``joinedload(Personnel.wage_type)`` to fetch the related
    WageType in the same query, avoiding N+1 problems when serialising
    personnel lists in API responses.
  - **Pagination**: ``get_all()`` supports offset/limit pagination with
    sensible defaults (skip=0, limit=100).
  - **Partial updates**: ``update()`` uses ``exclude_unset=True`` on the
    Pydantic model dump so that only the fields explicitly provided by
    the caller are modified — unmentioned fields retain their current
    database values.
"""

from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from ..models.personnel import Personnel, WageType


class PersonnelService:
    """Service class for personnel-related database operations.

    Follows the service-object pattern: instantiate with a SQLAlchemy
    ``Session``, then call methods to query or mutate personnel records.

    Attributes:
        db: The active SQLAlchemy session used for all queries.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Personnel]:
        """Get all personnel with their wage types eagerly loaded.

        Uses ``joinedload`` to fetch the related WageType in a single
        SQL JOIN, preventing lazy-load N+1 queries when the caller
        iterates over the results and accesses ``personnel.wage_type``.
        """
        return (
            self.db.query(Personnel)
            .options(joinedload(Personnel.wage_type))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_id(self, personnel_id: int) -> Optional[Personnel]:
        """Get a single personnel by ID with wage type eagerly loaded."""
        return (
            self.db.query(Personnel)
            .options(joinedload(Personnel.wage_type))
            .filter(Personnel.id == personnel_id)
            .first()
        )

    def create(
        self,
        name: str,
        wage_type_id: int,
        current_rate: float,
        phone: str | None = None,
        address: str | None = None,
        photo: str | None = None,
        salary_payment_date: int | None = None,
    ) -> Personnel:
        """Create a new personnel record."""
        db_personnel = Personnel(
            name=name,
            wage_type_id=wage_type_id,
            current_rate=current_rate,
            phone=phone,
            address=address,
            photo=photo,
            salary_payment_date=salary_payment_date,
        )
        self.db.add(db_personnel)
        self.db.commit()
        self.db.refresh(db_personnel)
        return db_personnel

    def update(
        self,
        personnel_id: int,
        name: str | None = None,
        wage_type_id: int | None = None,
        current_rate: float | None = None,
        phone: str | None = None,
        address: str | None = None,
        is_active: bool | None = None,
        photo: str | None = None,
        salary_payment_date: int | None = None,
    ) -> Optional[Personnel]:
        """Update an existing personnel record (partial update).

        Returns None if the personnel ID does not exist.
        """
        db_personnel = self.get_by_id(personnel_id)
        if not db_personnel:
            return None

        if name is not None:          db_personnel.name = name
        if wage_type_id is not None:  db_personnel.wage_type_id = wage_type_id
        if current_rate is not None:  db_personnel.current_rate = current_rate
        if phone is not None:         db_personnel.phone = phone
        if address is not None:       db_personnel.address = address
        if is_active is not None:     db_personnel.is_active = is_active
        if photo is not None:         db_personnel.photo = photo
        if salary_payment_date is not None: db_personnel.salary_payment_date = salary_payment_date

        self.db.commit()
        self.db.refresh(db_personnel)
        return db_personnel

    def delete(self, personnel_id: int) -> bool:
        """Delete a personnel record by ID.

        Returns True on successful deletion, False if no record with
        the given ID was found.  Note: this method queries the Personnel
        table directly (without ``joinedload``) since only the base
        record is needed for deletion.
        """
        db_personnel = self.db.query(Personnel).filter(Personnel.id == personnel_id).first()
        if not db_personnel:
            return False

        self.db.delete(db_personnel)
        self.db.commit()
        return True

    def pay_salary(self, personnel_id: int) -> str | Personnel:
        """Pay monthly salary for a personnel member. Creates a Labour expense."""
        from ..models.expense import Expense, ExpenseCategory
        from datetime import date, datetime, timedelta, timezone

        person = self.get_by_id(personnel_id)
        if not person:
            return "not_found"

        if not person.wage_type or person.wage_type.calculation_method != "MONTHLY":
            return "not_monthly"

        if not person.salary_payment_date:
            return "no_payment_date"

        today = date.today()
        payment_day = person.salary_payment_date
        if today.day >= payment_day:
            cycle_start_date = today.replace(day=payment_day)
        else:
            first_of_month = today.replace(day=1)
            prev_month = first_of_month - timedelta(days=1)
            cycle_start_date = prev_month.replace(day=payment_day)

        cycle_start = datetime.combine(cycle_start_date, datetime.min.time())

        already_paid = self.db.query(Expense).filter(
            Expense.personnel_id == personnel_id,
            Expense.date >= cycle_start,
        ).first()
        if already_paid:
            return "already_paid"

        labour_cat = self.db.query(ExpenseCategory).filter(
            ExpenseCategory.name == "Labour"
        ).first()
        if not labour_cat:
            return "labour_category_missing"

        expense = Expense(
            date=datetime.now(timezone.utc),
            amount=person.current_rate,
            category_id=labour_cat.id,
            personnel_id=personnel_id,
            description=f"Monthly salary for {person.name}",
        )
        self.db.add(expense)
        self.db.commit()
        self.db.refresh(person)
        return person

    def get_pending_salaries(self) -> list[dict]:
        """Return list of MONTHLY personnel with salary due within 5 days."""
        from ..models.expense import Expense
        from datetime import date, datetime, timedelta
        from dateutil.relativedelta import relativedelta

        today = date.today()
        monthly_personnel = (
            self.db.query(Personnel)
            .join(Personnel.wage_type)
            .filter(
                WageType.calculation_method == "MONTHLY",
                Personnel.is_active == True,
                Personnel.salary_payment_date.isnot(None),
            )
            .all()
        )

        pending = []
        for p in monthly_personnel:
            payment_day = p.salary_payment_date
            this_month_pd = today.replace(day=payment_day)

            if today.day >= payment_day:
                cycle_start = this_month_pd
                next_pd = this_month_pd + relativedelta(months=1)
            else:
                prev = this_month_pd - relativedelta(months=1)
                cycle_start = prev
                next_pd = this_month_pd

            days_until = (next_pd - today).days

            if days_until > 5:
                continue

            cycle_start_dt = datetime.combine(cycle_start, datetime.min.time())
            already_paid = self.db.query(Expense).filter(
                Expense.personnel_id == p.id,
                Expense.date >= cycle_start_dt,
            ).first()
            if already_paid:
                continue

            pending.append({
                "personnel_id": p.id,
                "personnel_name": p.name,
                "salary_amount": float(p.current_rate),
                "payment_due_date": str(next_pd),
                "days_until_due": days_until,
            })

        return pending

    def get_wage_types(self) -> List[WageType]:
        """Get all wage types.

        Convenience method that exposes WageType lookup through the
        PersonnelService.  The canonical CRUD for WageType (with
        create/update/delete) lives in ``SettingsService``.
        """
        return self.db.query(WageType).all()
