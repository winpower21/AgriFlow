from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..core.dependencies import get_current_user, roles_required
from ..crud.plantation import PlantationService
from ..database import get_db
from ..schemas.plantation import (
    DeleteCheckResponse,
    LeaseSchema,
    PlantationCreate,
    PlantationSchema,
    PlantationUpdate,
)

router = APIRouter(
    prefix="/plantations",
    tags=["plantations"],
    dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[PlantationSchema])
def get_all_plantations(db: Session = Depends(get_db)):
    """Get all plantations. Available to all authenticated users."""
    service = PlantationService(db)
    return service.get_all()


@router.get("/{plantation_id}", response_model=PlantationSchema)
def get_plantation(plantation_id: int, db: Session = Depends(get_db)):
    """Get a single plantation by ID. Available to all authenticated users."""
    service = PlantationService(db)
    plantation = service.get_by_id(plantation_id)
    if not plantation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plantation not found"
        )
    return plantation


@router.get("/{plantation_id}/lease-history", response_model=list[LeaseSchema])
def get_lease_history(plantation_id: int, db: Session = Depends(get_db)):
    """Get lease history for a plantation. Available to all authenticated users."""
    service = PlantationService(db)
    plantation = service.get_by_id(plantation_id)
    if not plantation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plantation not found"
        )
    return service.get_lease_history(plantation_id)


@router.get("/{plantation_id}/delete-check", response_model=DeleteCheckResponse)
def check_delete(plantation_id: int, db: Session = Depends(get_db)):
    """Check if a plantation has lease history before deleting."""
    service = PlantationService(db)
    plantation = service.get_by_id(plantation_id)
    if not plantation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plantation not found"
        )
    count = service.get_lease_history_count(plantation_id)
    return DeleteCheckResponse(has_history=count > 0, history_count=count)


@router.post(
    "/",
    response_model=PlantationSchema,
    status_code=201,
    dependencies=[Depends(roles_required("admin"))],
)
def create_plantation(data: PlantationCreate, db: Session = Depends(get_db)):
    """Create a new plantation. Admin only."""
    service = PlantationService(db)
    return service.create(data)


@router.put(
    "/{plantation_id}",
    response_model=PlantationSchema,
    dependencies=[Depends(roles_required("admin"))],
)
def update_plantation(
    plantation_id: int, data: PlantationUpdate, db: Session = Depends(get_db)
):
    """Update an existing plantation. Admin only.
    If lease dates change, the old lease is automatically archived to history."""
    service = PlantationService(db)
    plantation = service.update(plantation_id, data)
    if not plantation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plantation not found"
        )
    return plantation


@router.post(
    "/{plantation_id}/archive-lease",
    response_model=LeaseSchema,
    status_code=201,
    dependencies=[Depends(roles_required("admin"))],
)
def archive_current_lease(
    plantation_id: int,
    cost: float | None = None,
    db: Session = Depends(get_db),
):
    """Manually archive the current lease to history. Admin only."""
    service = PlantationService(db)
    history = service.archive_lease(plantation_id, cost=cost)
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plantation not found"
        )
    return history


@router.delete(
    "/{plantation_id}",
    status_code=204,
    dependencies=[Depends(roles_required("admin"))],
)
def delete_plantation(
    plantation_id: int,
    force: bool = Query(False, description="Force delete including lease history"),
    db: Session = Depends(get_db),
):
    """Delete a plantation. Admin only.
    If the plantation has lease history, force=true is required to confirm deletion."""
    service = PlantationService(db)
    result = service.delete(plantation_id, force=force)
    if result == "not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plantation not found"
        )
    if result == "has_history":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Plantation has lease history. Use force=true to delete with all history.",
        )
