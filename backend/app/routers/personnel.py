from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.dependencies import get_current_user
from ..crud.personnel import PersonnelService
from ..database import get_db
from ..schemas.personnel import (
    PersonnelCreate,
    PersonnelSchema,
    PersonnelUpdate,
    WageTypeSchema,
)

router = APIRouter(
    prefix="/personnel",
    tags=["personnel"],
    dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[PersonnelSchema])
def get_all_personnel(db: Session = Depends(get_db)):
    """Get all personnel."""
    service = PersonnelService(db)
    return service.get_all()


@router.get("/wage-types", response_model=list[WageTypeSchema])
def get_wage_types(db: Session = Depends(get_db)):
    """Get all wage types."""
    service = PersonnelService(db)
    return service.get_wage_types()


@router.get("/{personnel_id}", response_model=PersonnelSchema)
def get_personnel(personnel_id: int, db: Session = Depends(get_db)):
    """Get a single personnel by ID."""
    service = PersonnelService(db)
    person = service.get_by_id(personnel_id)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Personnel not found"
        )
    return person


@router.post("/", response_model=PersonnelSchema, status_code=201)
def create_personnel(data: PersonnelCreate, db: Session = Depends(get_db)):
    """Create a new personnel record."""
    service = PersonnelService(db)
    return service.create(data)


@router.put("/{personnel_id}", response_model=PersonnelSchema)
def update_personnel(
    personnel_id: int, data: PersonnelUpdate, db: Session = Depends(get_db)
):
    """Update an existing personnel record."""
    service = PersonnelService(db)
    person = service.update(personnel_id, data)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Personnel not found"
        )
    return person


@router.delete("/{personnel_id}", status_code=204)
def delete_personnel(personnel_id: int, db: Session = Depends(get_db)):
    """Delete a personnel record."""
    service = PersonnelService(db)
    deleted = service.delete(personnel_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Personnel not found"
        )
