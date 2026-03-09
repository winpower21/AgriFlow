"""
Central CRUD service registry for the AgriFlow application.

This module re-exports all CRUD service classes so that the rest of the
application can import them from a single location:

    from app.crud import UserService, PlantationService, ...

Each service follows a common pattern:
  - The constructor accepts a SQLAlchemy ``Session`` instance.
  - Methods encapsulate database queries and mutations for a specific
    domain entity (users, plantations, personnel, expenses, settings).
  - Callers (typically FastAPI route handlers) instantiate a service
    per-request using the ``get_db()`` dependency.

Note: ``WeatherCRUD`` and ``LocationCRUD`` from ``weather.py`` are *not*
re-exported here and must be imported directly from their module.
"""

from .expense import ExpenseService
from .personnel import PersonnelService
from .plantation import PlantationService
from .settings import SettingsService
from .user import UserService

__all__ = ["UserService", "PersonnelService", "PlantationService", "SettingsService", "ExpenseService"]
