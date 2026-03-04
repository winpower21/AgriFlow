from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..database import Base

if TYPE_CHECKING:
    from .plantation import Plantation
    from .weather import Weather


class Location(Base):
    """Location database model."""

    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    plantation_id: Mapped[int] = mapped_column(
        ForeignKey("plantations.id"), nullable=False
    )
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    city: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    state: Mapped[str] = mapped_column(String, nullable=True)
    country: Mapped[str] = mapped_column(String, nullable=True)
    latitude: Mapped[float] = mapped_column()
    longitude: Mapped[float] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    plantation: Mapped["Plantation"] = relationship(
        "Plantation", back_populates="location"
    )
    weather_data: Mapped[List["Weather"]] = relationship(
        "Weather", back_populates="location", cascade="all, delete-orphan"
    )
