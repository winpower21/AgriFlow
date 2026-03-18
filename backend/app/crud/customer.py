from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.customer import Customer
from ..models.sales import Sale
from ..schemas.customer import CustomerCreate


class CustomerService:
    def __init__(self, db: Session):
        self.db = db

    def search(self, q: str, limit: int = 20) -> list[Customer]:
        """Search customers by name or phone."""
        pattern = f"%{q}%"
        return (
            self.db.query(Customer)
            .filter(
                (Customer.name.ilike(pattern)) | (Customer.phone.ilike(pattern))
            )
            .limit(limit)
            .all()
        )

    def get_suggested(self, limit: int = 5) -> list[Customer]:
        """Return a mix of most-recent and most-frequent customers."""
        # 2 most recently created
        recent = (
            self.db.query(Customer)
            .order_by(Customer.created_at.desc())
            .limit(2)
            .all()
        )
        recent_ids = {c.id for c in recent}

        # Top customers by sale count, excluding those already in recent
        frequent_q = (
            self.db.query(Customer.id, func.count(Sale.id).label("cnt"))
            .join(Sale, Sale.customer_id == Customer.id)
            .group_by(Customer.id)
            .order_by(func.count(Sale.id).desc())
            .limit(limit)
            .all()
        )
        frequent_ids = [row[0] for row in frequent_q if row[0] not in recent_ids]

        if frequent_ids:
            frequent = (
                self.db.query(Customer)
                .filter(Customer.id.in_(frequent_ids))
                .all()
            )
        else:
            frequent = []

        # Combine, recent first, then frequent, up to limit
        result = list(recent)
        for c in frequent:
            if len(result) >= limit:
                break
            result.append(c)
        return result

    def get_by_id(self, customer_id: int) -> Optional[Customer]:
        return self.db.query(Customer).filter(Customer.id == customer_id).first()

    def get_by_phone(self, phone: str) -> Optional[Customer]:
        return self.db.query(Customer).filter(Customer.phone == phone).first()

    def create(self, data: CustomerCreate) -> Customer:
        customer = Customer(**data.model_dump())
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        return customer
