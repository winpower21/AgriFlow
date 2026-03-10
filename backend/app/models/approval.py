from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .user import User


class ApprovalRequest(Base):
    """Batch approval requests submitted by non-admin users."""

    __tablename__ = "approval_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(50))          # "EXPENSE" | "CONSUMABLE_PURCHASE"
    status: Mapped[str] = mapped_column(String(20), default="PENDING", index=True)  # PENDING | PARTIAL | RESOLVED
    requested_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    payload: Mapped[str] = mapped_column(Text)             # JSON string — array of items
    reviewed_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    requested_by: Mapped["User"] = relationship("User", foreign_keys=[requested_by_id])
    reviewed_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[reviewed_by_id])
