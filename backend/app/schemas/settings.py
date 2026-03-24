"""
Settings / lookup-table Pydantic schemas.

Defines CRUD schemas for the application-wide configuration entities that are
managed through the settings UI:

- **Wage Types** -- How workers are compensated (e.g. 'Daily', 'Piece-rate').
- **Batch Stages** -- The processing stages a batch can be in
  (e.g. HARVEST, CLEAN, DRY, BAG, GRADE, PACK, RETAIL).
- **Expense Categories** -- Categorisation labels for operational expenses
  (e.g. 'Fuel', 'Supplies', 'Maintenance').
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict

# ── Wage Type ────────────────────────────────────────


class WageTypeCreate(BaseModel):
    """Request body for creating a new wage type.

    Fields:
        name:               Label for the wage type (e.g. 'Daily', 'Piece-rate', 'Monthly').
        calculation_method: How wages are calculated ('DAILY', 'PER_KG', 'MONTHLY').
    """
    name: str
    calculation_method: str = "DAILY"


class WageTypeUpdate(BaseModel):
    """Request body for updating an existing wage type (PATCH-style).

    All fields are optional; only supplied fields are modified.
    """
    name: Optional[str] = None
    calculation_method: Optional[str] = None


class WageTypeSchema(BaseModel):
    """API response schema for a wage type record.

    Fields:
        id:                 Server-generated primary key.
        name:               Human-readable label for the wage type.
        calculation_method: How wages are calculated ('DAILY', 'PER_KG', 'MONTHLY').
    """
    id: int
    name: str
    calculation_method: str = "DAILY"

    model_config = ConfigDict(from_attributes=True)


# ── Batch Stage ──────────────────────────────────────


class BatchStageCreate(BaseModel):
    """Request body for creating a new batch processing stage.

    Fields:
        name: Label for the stage (e.g. 'HARVEST', 'CLEAN', 'DRY').
        is_salable: Whether batches at this stage can be sold.
        parent_id: Optional parent stage for hierarchy.
        sort_order: Display order among siblings.
        icon: Optional icon identifier.
        color: Optional hex color code.
    """
    name: str
    is_salable: bool = False
    parent_id: int | None = None
    sort_order: int = 0
    icon: str | None = None
    color: str | None = None
    is_waste: bool = False


class BatchStageUpdate(BaseModel):
    """Request body for updating an existing batch stage (PATCH-style).

    All fields are optional; only supplied fields are modified.
    """
    name: Optional[str] = None
    is_salable: Optional[bool] = None
    icon: str | None = None
    color: str | None = None
    is_waste: Optional[bool] = None


class BatchStageSchema(BaseModel):
    """API response schema for a batch stage record.

    Fields:
        id:   Server-generated primary key.
        name: Human-readable label for the processing stage.
        is_salable: Whether batches at this stage can be sold.
        parent_id: Parent stage ID for hierarchy.
        sort_order: Display order among siblings.
        batch_stage_level: Legacy level field (tree depth).
        icon: Icon identifier for dashboard display.
        color: Hex color code for dashboard display.
    """
    id: int
    name: str
    is_salable: bool
    parent_id: int | None = None
    sort_order: int = 0
    batch_stage_level: int | None = None
    icon: str | None = None
    color: str | None = None
    is_waste: bool = False

    model_config = ConfigDict(from_attributes=True)


class BatchStageReorderItem(BaseModel):
    """Schema for reordering batch stages."""
    id: int
    parent_id: int | None = None
    sort_order: int


# ── Expense Category ──────────────────────────────────────


class ExpenseCategoryCreate(BaseModel):
    """Request body for creating a new expense category.

    Fields:
        name:        Short label for the category (e.g. 'Fuel', 'Maintenance').
        description: Longer explanation of what expenses fall under this category.
    """
    name: str
    description: str


class ExpenseCategoryUpdate(BaseModel):
    """Request body for updating an existing expense category (PATCH-style).

    All fields are optional; only supplied fields are modified.
    """
    name: Optional[str] = None
    description: Optional[str] = None


class ExpenseCategorySchema(BaseModel):
    """API response schema for an expense category record.

    Fields:
        id:          Server-generated primary key.
        name:        Short label for the category.
        description: Longer explanation of the category's purpose.
    """
    id: int
    name: str
    description: str

    model_config = ConfigDict(from_attributes=True)


# ── App Config ────────────────────────────────────────────────────────────────


class AppConfigUpdate(BaseModel):
    """Request body for updating a single app config value."""

    value: str


class AppConfigSchema(BaseModel):
    """Response schema for a single app config key/value pair.

    Fields:
        key:   The setting identifier (e.g. 'hectares_to_acres_rate').
        value: The string value; callers parse/cast as needed.
    """

    key: str
    value: str

    model_config = ConfigDict(from_attributes=True)
