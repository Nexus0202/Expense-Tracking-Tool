from typing import List

from fastapi import APIRouter, status

from app.api.deps import DbDep
from app.schemas.budget import (
    BudgetCreate,
    BudgetResponse,
    BudgetStatusResponse,
    BudgetUpdate,
)
from app.services.budget_service import BudgetService

router = APIRouter(prefix="/budgets", tags=["Budgets"])


@router.post(
    "/",
    response_model=BudgetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a budget for a category and month",
)
def create_budget(data: BudgetCreate, db: DbDep) -> BudgetResponse:
    return BudgetResponse.model_validate(BudgetService.create(db, data))


@router.get(
    "/",
    response_model=List[BudgetResponse],
    summary="List all budgets",
)
def list_budgets(db: DbDep) -> List[BudgetResponse]:
    rows = BudgetService.list_all(db)
    return [BudgetResponse.model_validate(r) for r in rows]


@router.get(
    "/status",
    response_model=List[BudgetStatusResponse],
    summary="Budget vs actual spend with status per row",
)
def budget_status(db: DbDep) -> List[BudgetStatusResponse]:
    return BudgetService.build_status_list(db)


@router.put(
    "/{budget_id}",
    response_model=BudgetResponse,
    summary="Update a budget",
)
def update_budget(budget_id: str, data: BudgetUpdate, db: DbDep) -> BudgetResponse:
    return BudgetResponse.model_validate(BudgetService.update(db, budget_id, data))


@router.delete(
    "/{budget_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a budget",
)
def delete_budget(budget_id: str, db: DbDep) -> None:
    BudgetService.delete(db, budget_id)
