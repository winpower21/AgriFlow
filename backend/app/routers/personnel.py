"""
Personnel management router.

Provides full CRUD operations for personnel records (workers, staff, etc.)
plus a convenience endpoint for listing available wage types.

Endpoints
---------
GET    /personnel/                   — List all personnel records.
GET    /personnel/wage-types         — List all wage types (lookup data).
GET    /personnel/{personnel_id}     — Retrieve a single personnel record.
POST   /personnel/                   — Create a new personnel record.
PUT    /personnel/{personnel_id}     — Update an existing personnel record.
DELETE /personnel/{personnel_id}     — Delete a personnel record (204 No Content).

Authentication / authorisation
------------------------------
All endpoints require a valid JWT (any authenticated user).  The
``get_current_user`` dependency is applied at the **router level**, so
every endpoint inherits it automatically.  There is no additional
role-based restriction — any logged-in user can read and write personnel
data.

Request / response schemas
--------------------------
- ``PersonnelCreate`` — body for POST (name, wage_type_id, rate, etc.)
- ``PersonnelUpdate`` — body for PUT (partial update)
- ``PersonnelSchema`` — response model for a single personnel record
- ``WageTypeSchema``  — response model for wage type lookup entries
"""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ..config import settings
from ..core.dependencies import get_current_user
from ..crud.personnel import PersonnelService
from ..database import get_db
from ..schemas.personnel import (
    PersonnelSchema,
    WageTypeSchema,
)

# Auth: ``get_current_user`` is a router-level dependency — every endpoint
# underneath requires a valid JWT bearer token.  No role restriction.
router = APIRouter(
    prefix="/personnel",
    tags=["personnel"],
    dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)

ALLOWED_PHOTO_TYPES = {"image/jpeg", "image/png", "image/webp"}


def save_photo(file: UploadFile) -> str:
    """Validate, save uploaded photo to disk, return relative path."""
    if file.content_type not in ALLOWED_PHOTO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid file type '{file.content_type}'. Allowed: jpeg, png, webp.",
        )
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"
    dest = Path(settings.UPLOAD_DIR) / "personnel" / filename
    dest.write_bytes(file.file.read())
    return f"personnel/{filename}"


def delete_photo(relative_path: str | None) -> None:
    """Delete a photo file from disk if it exists."""
    if not relative_path:
        return
    path = Path(settings.UPLOAD_DIR) / relative_path
    path.unlink(missing_ok=True)


@router.get("/", response_model=list[PersonnelSchema])
def get_all_personnel(db: Session = Depends(get_db)):
    """Get all personnel records. Auth: any authenticated user."""
    service = PersonnelService(db)
    return service.get_all()


@router.get("/wage-types", response_model=list[WageTypeSchema])
def get_wage_types(db: Session = Depends(get_db)):
    """Get all wage types (convenience duplicate of settings/wage-types). Auth: any authenticated user."""
    service = PersonnelService(db)
    return service.get_wage_types()


@router.get("/{personnel_id}", response_model=PersonnelSchema)
def get_personnel(personnel_id: int, db: Session = Depends(get_db)):
    """Get a single personnel record by ID. Returns 404 if not found. Auth: any authenticated user."""
    service = PersonnelService(db)
    person = service.get_by_id(personnel_id)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Personnel not found"
        )
    return person


@router.post("/", response_model=PersonnelSchema, status_code=201)
def create_personnel(
    name: str = Form(...),
    wage_type_id: int = Form(...),
    current_rate: float = Form(...),
    phone: str | None = Form(None),
    address: str | None = Form(None),
    photo: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    """Create a new personnel record. Accepts multipart/form-data."""
    photo_path = save_photo(photo) if photo and photo.filename else None
    service = PersonnelService(db)
    return service.create(
        name=name,
        wage_type_id=wage_type_id,
        current_rate=current_rate,
        phone=phone,
        address=address,
        photo=photo_path,
    )


@router.put("/{personnel_id}", response_model=PersonnelSchema)
def update_personnel(
    personnel_id: int,
    name: str | None = Form(None),
    wage_type_id: int | None = Form(None),
    current_rate: float | None = Form(None),
    phone: str | None = Form(None),
    address: str | None = Form(None),
    is_active: bool | None = Form(None),
    photo: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    """Update an existing personnel record. Accepts multipart/form-data."""
    service = PersonnelService(db)
    person = service.get_by_id(personnel_id)
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Personnel not found")

    new_photo_path = None
    if photo and photo.filename:
        delete_photo(person.photo)           # remove old file from disk
        new_photo_path = save_photo(photo)

    return service.update(
        personnel_id=personnel_id,
        name=name,
        wage_type_id=wage_type_id,
        current_rate=current_rate,
        phone=phone,
        address=address,
        is_active=is_active,
        photo=new_photo_path,
    )


@router.delete("/{personnel_id}", status_code=204)
def delete_personnel(personnel_id: int, db: Session = Depends(get_db)):
    """Delete a personnel record. Returns 204 No Content on success, 404 if not found. Auth: any authenticated user."""
    service = PersonnelService(db)
    deleted = service.delete(personnel_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Personnel not found"
        )
