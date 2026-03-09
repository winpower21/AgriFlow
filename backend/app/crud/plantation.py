"""
Plantation CRUD service module.

Key changes from v1:
  - Location is no longer created inside create()/update(). The caller
    passes a ``location_id`` FK that points to an already-existing Location
    row (created via the /locations/resolve endpoint).
  - ``area_hectares`` and ``lease_cost`` are now included in create/update.
  - get_all() and get_by_id() use joinedload on ``lease`` and ``location``
    so that the ``is_active`` property (which iterates ``lease``) works
    without triggering lazy loads.
  - Weather cache methods: get_cached_weather() and save_weather().
  - Location search/resolve methods for the /locations endpoints.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from ..models.location import Location
from ..models.plantation import Plantation, PlantationLease
from ..models.weather import Weather
from ..schemas.plantation import (
    LeaseAddRequest,
    LeaseCreate,
    PlantationCreate,
    PlantationUpdate,
)

# Weather cache TTL — reuse existing rows fetched within this window.
_CACHE_TTL = timedelta(hours=6)


class PlantationService:
    """Service class for plantation-related database operations.

    Follows the service-object pattern: instantiate with a SQLAlchemy
    ``Session``, then call methods to query or mutate plantation records,
    their locations, and their lease history.

    Attributes:
        db: The active SQLAlchemy session used for all queries.
    """

    def __init__(self, db: Session):
        self.db = db

    def _base_query(self):
        """Base query with lease and location eagerly loaded.

        Required for ``is_active`` (iterates lease) and location display
        without additional queries.
        """
        return (
            self.db.query(Plantation)
            .options(joinedload(Plantation.lease), joinedload(Plantation.location))
        )

    def get_all(self) -> List[Plantation]:
        """Return all plantations ordered by ID with leases/location loaded."""
        return self._base_query().order_by(Plantation.id).all()

    def get_by_id(self, plantation_id: int) -> Optional[Plantation]:
        """Return a single plantation by PK with leases/location loaded."""
        return (
            self._base_query()
            .filter(Plantation.id == plantation_id)
            .first()
        )

    def create(self, data: PlantationCreate) -> Plantation:
        """Create a new plantation with optional initial lease.

        Location is referenced by ``location_id`` FK — no nested creation.
        If ``lease_start`` is provided, an initial PlantationLease row is
        appended in the same transaction.
        """
        obj = Plantation(
            name=data.name,
            location_id=data.location_id,
            area_hectares=data.area_hectares,
        )
        self.db.add(obj)
        # Flush to obtain the auto-generated plantation ID before creating
        # child rows in the same transaction.
        self.db.flush()

        # Append an initial lease if start date is supplied
        if data.lease_start:
            lease = PlantationLease(
                plantation_id=obj.id,
                start_date=data.lease_start,
                end_date=data.lease_end,
                cost=data.lease_cost,
            )
            self.db.add(lease)

        self.db.commit()
        # Reload with joinedload so is_active and location are populated
        return self.get_by_id(obj.id)

    def update(self, plantation_id: int, data: PlantationUpdate) -> Optional[Plantation]:
        """Partially update a plantation.

        Only fields explicitly set in the payload are applied
        (``exclude_unset=True``). Lease dates append a new PlantationLease
        row (append-only history) rather than overwriting the previous one.
        """
        obj = self.get_by_id(plantation_id)
        if not obj:
            return None

        updates = data.model_dump(exclude_unset=True)
        lease_start = updates.pop("lease_start", None)
        lease_end = updates.pop("lease_end", None)
        lease_cost = updates.pop("lease_cost", None)

        # Apply scalar field updates directly to the ORM object
        for field, value in updates.items():
            setattr(obj, field, value)

        # Append a new lease record if a start date was supplied
        if lease_start:
            lease = PlantationLease(
                plantation_id=obj.id,
                start_date=lease_start,
                end_date=lease_end,
                cost=lease_cost,
            )
            self.db.add(lease)

        self.db.commit()
        return self.get_by_id(plantation_id)

    def delete(self, plantation_id: int, force: bool = False) -> Optional[str]:
        """Delete a plantation with optional force override.

        Returns None on success, or an error string:
          - ``"not_found"`` — no plantation with the given ID exists.
          - ``"has_history"`` — the plantation has lease records and
            ``force`` was not True.
        """
        obj = self.get_by_id(plantation_id)
        if not obj:
            return "not_found"

        history_count = self.get_lease_history_count(plantation_id)
        if history_count > 0 and not force:
            return "has_history"

        self.db.delete(obj)
        self.db.commit()
        return None

    def get_lease_history_count(self, plantation_id: int) -> int:
        """Return the number of lease records associated with a plantation."""
        return (
            self.db.query(PlantationLease)
            .filter(PlantationLease.plantation_id == plantation_id)
            .count()
        )

    # ── Lease History ─────────────────────────────────────────────────────────

    def get_lease_history(self, plantation_id: int) -> List[PlantationLease]:
        """Return all lease records for a plantation, newest first."""
        return (
            self.db.query(PlantationLease)
            .filter(PlantationLease.plantation_id == plantation_id)
            .order_by(PlantationLease.start_date.desc())
            .all()
        )

    def create_lease_history(self, data: LeaseCreate) -> PlantationLease:
        """Append a new lease period to a plantation's history (standalone endpoint)."""
        obj = PlantationLease(**data.model_dump())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def add_lease(self, plantation_id: int, data: LeaseAddRequest) -> Optional[PlantationLease]:
        """Append a lease from the detail modal (plantation_id comes from URL).

        Returns None if the plantation does not exist.
        """
        obj = self.get_by_id(plantation_id)
        if not obj:
            return None
        lease = PlantationLease(
            plantation_id=plantation_id,
            start_date=data.start_date,
            end_date=data.end_date,
            cost=data.cost,
        )
        self.db.add(lease)
        self.db.commit()
        self.db.refresh(lease)
        return lease

    # ── Location search ───────────────────────────────────────────────────────

    def search_locations_db(self, query: str) -> List[Location]:
        """Search existing Location rows by city name (case-insensitive partial match).

        Returns up to 5 matching rows ordered by city name.
        """
        return (
            self.db.query(Location)
            .filter(Location.city.ilike(f"%{query}%"))
            .order_by(Location.city)
            .limit(5)
            .all()
        )

    def resolve_location_from_place(
        self,
        city: str,
        state: Optional[str],
        country: Optional[str],
        latitude: float,
        longitude: float,
    ) -> Location:
        """Upsert a Location from Google Place Details and return it.

        If a Location with the same city already exists, returns the existing
        row (updating lat/lng in case they changed).  Otherwise inserts a
        new row.
        """
        existing = (
            self.db.query(Location)
            .filter(Location.city == city)
            .first()
        )
        if existing:
            existing.latitude = latitude
            existing.longitude = longitude
            self.db.commit()
            self.db.refresh(existing)
            return existing

        loc = Location(
            city=city,
            state=state,
            country=country,
            latitude=latitude,
            longitude=longitude,
        )
        self.db.add(loc)
        self.db.commit()
        self.db.refresh(loc)
        return loc

    # ── Weather cache ─────────────────────────────────────────────────────────

    def get_cached_weather(self, location_id: int) -> Optional[Weather]:
        """Return the most recent Weather row if it is within the 6-hour TTL.

        The TTL check applies to all rows regardless of ``is_manual`` — a
        manually-fetched record also satisfies an auto-fetch cache hit.
        Returns None if no fresh row exists (caller should fetch from API).
        """
        cutoff = datetime.now(timezone.utc) - _CACHE_TTL
        return (
            self.db.query(Weather)
            .filter(
                Weather.location_id == location_id,
                Weather.fetched_at >= cutoff,
            )
            .order_by(Weather.fetched_at.desc())
            .first()
        )

    def save_weather(
        self, location_id: int, raw_json: dict, is_manual: bool = False
    ) -> Weather:
        """Insert a new Weather row (append-only — never overwrites existing rows).

        Args:
            location_id: FK to the Location this observation covers.
            raw_json:    Combined dict with 'current' and 'hourly' keys from
                         Google Weather API responses.
            is_manual:   True when triggered by the user's refresh button.
        """
        record = Weather(
            location_id=location_id,
            raw_json=raw_json,
            is_manual=is_manual,
            fetched_at=datetime.now(timezone.utc),
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record
