from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ..core.dependencies import get_current_user, roles_required
from ..crud.vehicle import VehicleService
from ..database import get_db
from ..schemas.vehicle import VehicleCreate, VehicleSchema, VehicleUpdate
from ..schemas.response import ApiResponse

router = APIRouter(
    prefix="/vehicles",
    tags=["vehicles"],
    dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=ApiResponse[list[VehicleSchema]])
def get_vehicles(
    search: Optional[str] = Query(None),
    active_only: bool = Query(False),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=VehicleService(db).get_all(search=search, active_only=active_only))


@router.post("/", response_model=ApiResponse[VehicleSchema], status_code=201,
             dependencies=[Depends(roles_required("admin"))])
def create_vehicle(data: VehicleCreate, db: Session = Depends(get_db)):
    return ApiResponse(data=VehicleService(db).create(data), message="Vehicle added successfully", type="success")


@router.put("/{vehicle_id}", response_model=ApiResponse[VehicleSchema],
            dependencies=[Depends(roles_required("admin"))])
def update_vehicle(vehicle_id: int, data: VehicleUpdate, db: Session = Depends(get_db)):
    result = VehicleService(db).update(vehicle_id, data)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    return ApiResponse(data=result, message="Vehicle updated successfully", type="success")


@router.delete("/{vehicle_id}", response_model=ApiResponse[VehicleSchema],
               dependencies=[Depends(roles_required("admin"))])
def toggle_vehicle_active(vehicle_id: int, db: Session = Depends(get_db)):
    result = VehicleService(db).toggle_active(vehicle_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    return ApiResponse(data=result, message="Vehicle status updated", type="success")
