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
    ) -> Personnel:
        """Create a new personnel record."""
        db_personnel = Personnel(
            name=name,
            wage_type_id=wage_type_id,
            current_rate=current_rate,
            phone=phone,
            address=address,
            photo=photo,
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

    def get_wage_types(self) -> List[WageType]:
        """Get all wage types.

        Convenience method that exposes WageType lookup through the
        PersonnelService.  The canonical CRUD for WageType (with
        create/update/delete) lives in ``SettingsService``.
        """
        return self.db.query(WageType).all()
