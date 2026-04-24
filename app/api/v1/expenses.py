from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query, status

from app.api.deps import DbDep
from app.schemas.common import PaginatedResponse
from app.schemas.expense import ExpenseCreate, ExpenseResponse, ExpenseUpdate
from app.services.expense_service import ExpenseService

router = APIRouter(prefix="/expenses", tags=["Expenses"])


@router.post(
    "/",
    response_model=ExpenseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new expense",
)
def create_expense(data: ExpenseCreate, db: DbDep) -> ExpenseResponse:
    """Add a single expense record manually."""
    return ExpenseService.create(db, data)


@router.get(
    "/",
    response_model=PaginatedResponse[ExpenseResponse],
    summary="List expenses with filters and pagination",
)
def list_expenses(
    db: DbDep,
    start_date: Optional[datetime] = Query(None, description="Filter from this date (ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="Filter up to this date (ISO 8601)"),
    category: Optional[str] = Query(None, description="Partial category name match"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
) -> PaginatedResponse[ExpenseResponse]:
    """
    Return a paginated list of expenses.
    Optionally filter by date range and/or category (case-insensitive partial match).
    """
    items, total = ExpenseService.get_all(db, start_date, end_date, category, page, page_size)
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get(
    "/{expense_id}",
    response_model=ExpenseResponse,
    summary="Get a single expense by ID",
)
def get_expense(expense_id: str, db: DbDep) -> ExpenseResponse:
    """Fetch one expense by its UUID. Returns 404 if not found."""
    return ExpenseService.get_by_id(db, expense_id)


@router.patch(
    "/{expense_id}",
    response_model=ExpenseResponse,
    summary="Partially update an expense",
)
def update_expense(expense_id: str, data: ExpenseUpdate, db: DbDep) -> ExpenseResponse:
    """Update one or more fields of an existing expense. Unset fields are left unchanged."""
    return ExpenseService.update(db, expense_id, data)


@router.delete(
    "/{expense_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an expense",
)
def delete_expense(expense_id: str, db: DbDep) -> None:
    """Permanently delete an expense by ID."""
    ExpenseService.delete(db, expense_id)
