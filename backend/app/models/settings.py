"""
AppConfig model — application-wide key/value settings store.

Used for scalar configuration values that administrators can change at
runtime without a code deploy (e.g. unit conversion rates).  Each row
is identified by a unique string key; the value is stored as text and
parsed by the caller.
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class AppConfig(Base):
    """Single-row-per-key settings store.

    Fields:
        key:   Unique identifier for the setting (e.g. 'hectares_to_acres_rate').
        value: String representation of the value; callers cast as needed.
    """

    __tablename__ = "app_config"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(String, nullable=False)
