from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from ..models.personnel import Personnel, WageType
from ..schemas.personnel import PersonnelCreate, PersonnelUpdate


class PersonnelService:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Personnel]:
        """Get all personnel with their wage types."""
        return (
            self.db.query(Personnel)
            .options(joinedload(Personnel.wage_type))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_id(self, personnel_id: int) -> Optional[Personnel]:
        """Get a single personnel by ID."""
        return (
            self.db.query(Personnel)
            .options(joinedload(Personnel.wage_type))
            .filter(Personnel.id == personnel_id)
            .first()
        )

    def create(self, data: PersonnelCreate) -> Personnel:
        """Create a new personnel record."""
        db_personnel = Personnel(**data.model_dump())
        self.db.add(db_personnel)
        self.db.commit()
        self.db.refresh(db_personnel)
        return db_personnel

    def update(self, personnel_id: int, data: PersonnelUpdate) -> Optional[Personnel]:
        """Update an existing personnel record."""
        db_personnel = self.get_by_id(personnel_id)
        if not db_personnel:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_personnel, field, value)

        self.db.commit()
        self.db.refresh(db_personnel)
        return db_personnel

    def delete(self, personnel_id: int) -> bool:
        """Delete a personnel record."""
        db_personnel = self.db.query(Personnel).filter(Personnel.id == personnel_id).first()
        if not db_personnel:
            return False

        self.db.delete(db_personnel)
        self.db.commit()
        return True

    def get_wage_types(self) -> List[WageType]:
        """Get all wage types."""
        return self.db.query(WageType).all()
