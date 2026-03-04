from typing import List, Optional

from sqlalchemy.orm import Session

from ..models.location import Location
from ..models.plantation import Plantation, PlantationLease
from ..schemas.plantation import (
    LeaseCreate,
    PlantationCreate,
    PlantationUpdate,
)


class PlantationService:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[Plantation]:
        return self.db.query(Plantation).order_by(Plantation.id).all()

    def get_by_id(self, plantation_id: int) -> Optional[Plantation]:
        return self.db.query(Plantation).filter(Plantation.id == plantation_id).first()

    def create(self, data: PlantationCreate) -> Plantation:
        dump = data.model_dump()
        location_data = dump.pop("location", None)
        obj = Plantation(**dump)
        self.db.add(obj)
        self.db.flush()

        if location_data:
            loc = Location(plantation_id=obj.id, **location_data)
            self.db.add(loc)

        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(
        self, plantation_id: int, data: PlantationUpdate
    ) -> Optional[Plantation]:
        obj = self.get_by_id(plantation_id)
        if not obj:
            return None

        updates = data.model_dump(exclude_unset=True)
        location_data = updates.pop("location", None)

        # Auto-archive: if lease dates are changing, archive the old lease
        lease_changing = "lease_start" in updates or "lease_end" in updates
        if lease_changing:
            new_start = updates.get("lease_start", obj.lease_start)
            new_end = updates.get("lease_end", obj.lease_end)
            # Only archive if dates actually differ from current
            if new_start != obj.lease_start or new_end != obj.lease_end:
                self._archive_current_lease(obj)

        for field, value in updates.items():
            setattr(obj, field, value)

        if location_data is not None:
            if obj.location:
                for field, value in location_data.items():
                    setattr(obj.location, field, value)
            else:
                loc = Location(plantation_id=obj.id, **location_data)
                self.db.add(loc)

        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, plantation_id: int, force: bool = False) -> Optional[str]:
        """Delete a plantation.

        Returns None on success, or an error message string.
        If the plantation has lease history and force=False,
        returns an error indicating confirmation is required.
        """
        obj = self.get_by_id(plantation_id)
        if not obj:
            return "not_found"

        history_count = self.get_lease_history_count(plantation_id)
        if history_count > 0 and not force:
            return "has_history"

        # cascade will delete lease history due to cascade="all, delete-orphan"
        self.db.delete(obj)
        self.db.commit()
        return None

    def get_lease_history_count(self, plantation_id: int) -> int:
        return (
            self.db.query(PlantationLease)
            .filter(PlantationLease.plantation_id == plantation_id)
            .count()
        )

    # ── Lease History ────────────────────────────────

    def _archive_current_lease(self, plantation: Plantation, cost=None):
        """Archive the current lease period to history."""
        history = PlantationLease(
            plantation_id=plantation.id,
            start_date=plantation.lease_start,
            end_date=plantation.lease_end,
            cost=cost,
        )
        self.db.add(history)

    def archive_lease(self, plantation_id: int, cost=None) -> Optional[PlantationLease]:
        """Manually archive the current lease of a plantation."""
        obj = self.get_by_id(plantation_id)
        if not obj:
            return None
        history = PlantationLease(
            plantation_id=obj.id,
            start_date=obj.lease_start,
            end_date=obj.lease_end,
            cost=cost,
        )
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)
        return history

    def get_lease_history(self, plantation_id: int) -> List[PlantationLease]:
        return (
            self.db.query(PlantationLease)
            .filter(PlantationLease.plantation_id == plantation_id)
            .order_by(PlantationLease.start_date.desc())
            .all()
        )

    def create_lease_history(self, data: LeaseCreate) -> PlantationLease:
        obj = PlantationLease(**data.model_dump())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj
