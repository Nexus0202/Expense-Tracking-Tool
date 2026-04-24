import math
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, computed_field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int

    @computed_field  # type: ignore[misc]
    @property
    def total_pages(self) -> int:
        return math.ceil(self.total / self.page_size) if self.total else 0


class CategorySummary(BaseModel):
    category: str
    total: float
    count: int


class MonthlySummary(BaseModel):
    year: int
    month: int
    total: float
    count: int


class DashboardSummary(BaseModel):
    total_expenses: float
    total_count: int
    by_category: List[CategorySummary]
    by_month: List[MonthlySummary]


class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None
