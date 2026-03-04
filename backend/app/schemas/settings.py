from typing import Optional

from pydantic import BaseModel, ConfigDict

# ── Wage Type ────────────────────────────────────────


class WageTypeCreate(BaseModel):
    name: str


class WageTypeUpdate(BaseModel):
    name: Optional[str] = None


class WageTypeSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


# ── Batch Stage ──────────────────────────────────────


class BatchStageCreate(BaseModel):
    name: str


class BatchStageUpdate(BaseModel):
    name: Optional[str] = None


class BatchStageSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


# ── Expense Category ──────────────────────────────────────
class ExpenseCategoryCreate(BaseModel):
    name: str
    description: str


class ExpenseCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ExpenseCategorySchema(BaseModel):
    id: int
    name: str
    description: str

    model_config = ConfigDict(from_attributes=True)
