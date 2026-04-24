from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ExpenseBase(BaseModel):
    amount: float = Field(..., gt=0, description="Expense amount — must be positive")
    category: str = Field(..., min_length=1, max_length=100, examples=["Food"])
    description: Optional[str] = Field(None, max_length=500)
    date: datetime = Field(..., description="Date of the expense (ISO 8601)")


class ExpenseCreate(ExpenseBase):
    source: Literal["manual", "pdf"] = Field("manual", description="Origin of the record")


class ExpenseUpdate(BaseModel):
    """All fields are optional — only provided fields are updated."""

    amount: Optional[float] = Field(None, gt=0)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    date: Optional[datetime] = None


class ExpenseResponse(ExpenseBase):
    id: str
    source: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
