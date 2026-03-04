from ..database import Base
from .batch import Batch, BatchStage
from .consumables import (
    Consumable,
    ConsumableConsumption,
    ConsumablePurchase,
    ConsumptionAllocation,
)
from .expense import Expense, ExpenseCategory
from .location import Location
from .personnel import Personnel, TransformationPersonnel, WageType
from .plantation import Plantation, PlantationLease
from .sales import RetailInventory, Sale, SaleAllocation
from .transformation import (
    Transformation,
    TransformationInput,
    TransformationOutput,
    TransformationType,
)
from .user import Role, User
from .vehicle import TransformationVehicle, Vehicle
from .weather import Weather

# Import all models here so Alembic can discover them
__all__ = [
    "Base",
    "User",
    "Role",
    "Plantation",
    "PlantationLease",
    "Vehicle",
    "Personnel",
    "WageType",
    "Consumable",
    "Batch",
    "BatchStage",
    "TransformationType",
    "Transformation",
    "TransformationInput",
    "TransformationOutput",
    "TransformationPersonnel",
    "ConsumablePurchase",
    "ConsumableConsumption",
    "ConsumptionAllocation",
    "TransformationVehicle",
    "Sale",
    "SaleAllocation",
    "RetailInventory",
    "Expense",
    "ExpenseCategory",
    "Location",
    "Weather",
]
