from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class BudgetCreate(BaseModel):
    category: str = Field(..., min_length=1, max_length=100, examples=["Food"])
    amount: float = Field(..., gt=0, description="Monthly budget limit")
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2000, le=2100)


class BudgetUpdate(BaseModel):
    """Only provided fields are applied on update."""

    category: Optional[str] = Field(None, min_length=1, max_length=100)
    amount: Optional[float] = Field(None, gt=0)
    month: Optional[int] = Field(None, ge=1, le=12)
    year: Optional[int] = Field(None, ge=2000, le=2100)


class BudgetResponse(BaseModel):
    id: str
    category: str
    amount: float
    month: int
    year: int
    created_at: datetime

    model_config = {"from_attributes": True}


class BudgetStatusResponse(BaseModel):
    """Per-budget row with live spent totals from expenses."""

    id: str
    category: str
    month: int
    year: int
    budget: float = Field(..., description="Planned limit for the period")
    spent: float
    remaining: float
    percentage_used: float
    status: Literal["safe", "warning", "danger"]
