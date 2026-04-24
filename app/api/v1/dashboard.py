from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query

from app.api.deps import DbDep
from app.schemas.common import DashboardSummary
from app.services.expense_service import ExpenseService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/summary",
    response_model=DashboardSummary,
    summary="Aggregated expense summary",
)
def get_summary(
    db: DbDep,
    start_date: Optional[datetime] = Query(None, description="Summarise from this date"),
    end_date: Optional[datetime] = Query(None, description="Summarise up to this date"),
) -> DashboardSummary:
    """
    Returns:
    - **total_expenses**: sum of all matching expenses
    - **total_count**: number of matching expense records
    - **by_category**: breakdown per category (sorted descending by total)
    - **by_month**: chronological monthly breakdown
    """
    return ExpenseService.get_summary(db, start_date, end_date)
