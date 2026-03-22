"""
Central schema registry for the AgriFlow application.

This module re-exports all Pydantic schemas used across the API so that other
parts of the application can import them from a single location:

    from app.schemas import UserCreate, PlantationSchema, ...

Schemas are organised into sub-modules by domain entity (user, role, token,
plantation, batch, transformation, personnel, expense, location, weather,
settings).  The ``__all__`` list controls what is publicly available when a
wildcard import (``from app.schemas import *``) is used.
"""

from .expense import ExpenseCreate, ExpenseSchema
from .location import LocationCreateSchema, LocationSchema
from .personnel import PersonnelCreate, PersonnelSchema, PersonnelUpdate, WageTypeSchema
from .plantation import (
    DeleteCheckResponse,
    LeaseCreate,
    LeaseSchema,
    PlantationCreate,
    PlantationSchema,
    PlantationUpdate,
)
from .role import Role
from .settings import (
    BatchStageCreate,
    BatchStageSchema,
    BatchStageUpdate,
    ExpenseCategoryCreate,
    ExpenseCategorySchema,
    ExpenseCategoryUpdate,
    WageTypeCreate,
    WageTypeUpdate,
)
from .settings import (
    WageTypeSchema as SettingsWageTypeSchema,
)
from .transformation import (
    TransformationTypeCreate,
    TransformationTypeSchema,
    TransformationTypeUpdate,
)
from .token import Token, TokenData, TokenWithUser
from .user import RoleChange, User, UserCreate, UserInDB, UserUpdate
from .weather import WeatherSchema
from .response import ApiResponse, success_response

__all__ = [
    "User",
    "UserCreate",
    "UserUpdate",
    "UserInDB",
    "RoleChange",
    "Role",
    "LocationCreateSchema",
    "WeatherSchema",
    "LocationSchema",
    "Token",
    "TokenData",
    "TokenWithUser",
    "PersonnelSchema",
    "PersonnelCreate",
    "PersonnelUpdate",
    "WageTypeSchema",
    "TransformationTypeSchema",
    "TransformationTypeCreate",
    "TransformationTypeUpdate",
    "SettingsWageTypeSchema",
    "WageTypeCreate",
    "WageTypeUpdate",
    "BatchStageSchema",
    "BatchStageCreate",
    "BatchStageUpdate",
    "PlantationSchema",
    "PlantationCreate",
    "PlantationUpdate",
    "LeaseSchema",
    "LeaseCreate",
    "DeleteCheckResponse",
    "ExpenseCategorySchema",
    "ExpenseCategoryCreate",
    "ExpenseCategoryUpdate",
    "ExpenseSchema",
    "ExpenseCreate",
]
