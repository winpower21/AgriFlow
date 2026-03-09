"""
Weather observation model.

Append-only: every API fetch (auto or manual) inserts a new row.
Cache hit = latest row for a location with fetched_at > now() - 6h.
Manual refresh bypasses the TTL and always inserts a new row
(is_manual=True).  Old rows are never modified or deleted, giving a
full historical record for future transformation analysis.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..database import Base

if TYPE_CHECKING:
    from .location import Location


class Weather(Base):
    """Append-only weather record linked to a geographic location."""

    __tablename__ = "weather"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # FK to the location this observation covers
    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id"), nullable=False, index=True
    )

    # When this record was fetched from the Google Weather API (indexed
    # for efficient TTL queries: WHERE fetched_at > now() - interval '6h')
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    # True when the user explicitly triggered the refresh; False for
    # automatic cache-miss fetches.  Useful for historical provenance.
    is_manual: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Full raw JSON from the Google Weather API response stored as JSONB.
    # Keeps all fields (temperature, feels_like, wind, UV, etc.) for
    # future transformation analysis without requiring schema changes.
    raw_json: Mapped[dict] = mapped_column(JSONB, nullable=False)

    location: Mapped["Location"] = relationship(
        "Location", back_populates="weather_data"
    )
