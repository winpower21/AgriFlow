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
from ..core.dependencies import get_current_user, roles_required
from ..crud.personnel import PersonnelService
from ..database import get_db
from ..schemas.personnel import (
    PersonnelSchema,
    WageTypeSchema,
)
from ..schemas.response import ApiResponse

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


def _validate_phone(phone: str | None):
    """Validate phone number format if provided."""
    if phone is None:
        return
    if not phone.isdigit():
        raise HTTPException(status_code=422, detail="Phone must contain only digits")
    if len(phone) != 10:
        raise HTTPException(status_code=422, detail="Phone must be exactly 10 digits")
    if phone.startswith("0"):
        raise HTTPException(status_code=422, detail="Phone must not start with 0")


@router.get("/", response_model=ApiResponse[list[PersonnelSchema]])
def get_all_personnel(db: Session = Depends(get_db)):
    """Get all personnel records. Auth: any authenticated user."""
    service = PersonnelService(db)
    return ApiResponse(data=service.get_all())


@router.get("/wage-types", response_model=ApiResponse[list[WageTypeSchema]])
def get_wage_types(db: Session = Depends(get_db)):
    """Get all wage types (convenience duplicate of settings/wage-types). Auth: any authenticated user."""
    service = PersonnelService(db)
    return ApiResponse(data=service.get_wage_types())


@router.get("/pending-salaries")
def get_pending_salaries(
    db: Session = Depends(get_db),
):
    service = PersonnelService(db)
    return ApiResponse(data=service.get_pending_salaries(), message="", type="success")


@router.get("/{personnel_id}", response_model=ApiResponse[PersonnelSchema])
def get_personnel(personnel_id: int, db: Session = Depends(get_db)):
    """Get a single personnel record by ID. Returns 404 if not found. Auth: any authenticated user."""
    service = PersonnelService(db)
    person = service.get_by_id(personnel_id)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Personnel not found"
        )
    return ApiResponse(data=person)


@router.post("/", response_model=ApiResponse[PersonnelSchema], status_code=201,
             dependencies=[Depends(roles_required("admin"))])
def create_personnel(
    name: str = Form(...),
    wage_type_id: int = Form(...),
    current_rate: float = Form(...),
    phone: str | None = Form(None),
    address: str | None = Form(None),
    salary_payment_date: int | None = Form(None),
    photo: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    """Create a new personnel record. Accepts multipart/form-data."""
    _validate_phone(phone)
    if salary_payment_date is not None and not (1 <= salary_payment_date <= 28):
        raise HTTPException(status_code=422, detail="salary_payment_date must be between 1 and 28")
    photo_path = save_photo(photo) if photo and photo.filename else None
    service = PersonnelService(db)
    return ApiResponse(
        data=service.create(
            name=name,
            wage_type_id=wage_type_id,
            current_rate=current_rate,
            phone=phone,
            address=address,
            salary_payment_date=salary_payment_date,
            photo=photo_path,
        ),
        message="Personnel added successfully",
        type="success",
    )


@router.put("/{personnel_id}", response_model=ApiResponse[PersonnelSchema],
            dependencies=[Depends(roles_required("admin"))])
def update_personnel(
    personnel_id: int,
    name: str | None = Form(None),
    wage_type_id: int | None = Form(None),
    current_rate: float | None = Form(None),
    phone: str | None = Form(None),
    address: str | None = Form(None),
    is_active: bool | None = Form(None),
    salary_payment_date: int | None = Form(None),
    photo: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    """Update an existing personnel record. Accepts multipart/form-data."""
    _validate_phone(phone)
    if salary_payment_date is not None and not (1 <= salary_payment_date <= 28):
        raise HTTPException(status_code=422, detail="salary_payment_date must be between 1 and 28")
    service = PersonnelService(db)
    person = service.get_by_id(personnel_id)
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Personnel not found")

    new_photo_path = None
    if photo and photo.filename:
        delete_photo(person.photo)           # remove old file from disk
        new_photo_path = save_photo(photo)

    return ApiResponse(
        data=service.update(
            personnel_id=personnel_id,
            name=name,
            wage_type_id=wage_type_id,
            current_rate=current_rate,
            phone=phone,
            address=address,
            is_active=is_active,
            salary_payment_date=salary_payment_date,
            photo=new_photo_path,
        ),
        message="Personnel updated successfully",
        type="success",
    )


@router.post("/{personnel_id}/pay-salary", response_model=ApiResponse[PersonnelSchema],
              dependencies=[Depends(roles_required("admin"))])
def pay_salary(
    personnel_id: int,
    db: Session = Depends(get_db),
):
    service = PersonnelService(db)
    result = service.pay_salary(personnel_id)
    if result == "not_found":
        raise HTTPException(status_code=404, detail="Personnel not found")
    if result == "not_monthly":
        raise HTTPException(status_code=422, detail="Personnel is not on monthly salary")
    if result == "no_payment_date":
        raise HTTPException(status_code=422, detail="No salary payment date configured")
    if result == "already_paid":
        raise HTTPException(status_code=409, detail="Salary already paid for current cycle")
    if result == "labour_category_missing":
        raise HTTPException(status_code=500, detail="Labour expense category not found")
    return ApiResponse(data=result, message="Salary paid successfully", type="success")


@router.delete("/{personnel_id}", response_model=ApiResponse[None],
               dependencies=[Depends(roles_required("admin"))])
def delete_personnel(personnel_id: int, db: Session = Depends(get_db)):
    """Delete a personnel record. Returns 200 with ApiResponse on success, 404 if not found. Auth: any authenticated user."""
    service = PersonnelService(db)
    deleted = service.delete(personnel_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Personnel not found"
        )
    return ApiResponse(data=None, message="Personnel deleted successfully", type="success")
