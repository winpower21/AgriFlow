from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..database import Base

if TYPE_CHECKING:
    from .location import Location


class Weather(Base):
    """Weather data database model."""

    __tablename__ = "weather"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    temperature_c: Mapped[float] = mapped_column()
    humidity_percent: Mapped[float] = mapped_column()
    precipitation_mm: Mapped[float] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    location: Mapped["Location"] = relationship(
        "Location", back_populates="weather_data"
    )
