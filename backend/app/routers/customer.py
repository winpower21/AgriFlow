from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..core.dependencies import get_current_user
from ..crud.customer import CustomerService
from ..database import get_db
from ..schemas.customer import CustomerCreate, CustomerSchema

router = APIRouter(
    prefix="/customers",
    tags=["customers"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/suggested", response_model=list[CustomerSchema])
def suggested_customers(db: Session = Depends(get_db)):
    """Return recent + frequent customers for quick selection."""
    return CustomerService(db).get_suggested()


@router.get("/search", response_model=list[CustomerSchema])
def search_customers(
    q: str = Query("", min_length=1),
    db: Session = Depends(get_db),
):
    return CustomerService(db).search(q)


@router.post("/", response_model=CustomerSchema, status_code=status.HTTP_201_CREATED)
def create_customer(data: CustomerCreate, db: Session = Depends(get_db)):
    svc = CustomerService(db)
    existing = svc.get_by_phone(data.phone)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Customer with this phone number already exists",
        )
    return svc.create(data)
