from typing import List, Optional

from sqlalchemy.orm import Session

from ..models.vehicle import Vehicle
from ..schemas.vehicle import VehicleCreate, VehicleUpdate


class VehicleService:
    def __init__(self, db: Session):
        self.db = db

    def get_all(
        self, search: Optional[str] = None, active_only: bool = False
    ) -> List[Vehicle]:
        q = self.db.query(Vehicle)
        if active_only:
            q = q.filter(Vehicle.is_active)
        if search:
            q = q.filter(Vehicle.number.ilike(f"%{search}%"))
        return q.order_by(Vehicle.number).all()

    def get_by_id(self, vehicle_id: int) -> Optional[Vehicle]:
        return self.db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()

    def create(self, data: VehicleCreate) -> Vehicle:
        obj = Vehicle(**data.model_dump())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, vehicle_id: int, data: VehicleUpdate) -> Optional[Vehicle]:
        obj = self.get_by_id(vehicle_id)
        if not obj:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def toggle_active(self, vehicle_id: int) -> Optional[Vehicle]:
        obj = self.get_by_id(vehicle_id)
        if not obj:
            return None
        obj.is_active = not obj.is_active
        self.db.commit()
        self.db.refresh(obj)
        return obj
