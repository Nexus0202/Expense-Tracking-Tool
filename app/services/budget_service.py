import logging
import uuid
from typing import Dict, List, Literal, Tuple

from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.models.budget import Budget
from app.models.expense import Expense
from app.schemas.budget import BudgetCreate, BudgetStatusResponse, BudgetUpdate
from app.utils.exceptions import BudgetNotFoundError

logger = logging.getLogger(__name__)

# Status thresholds: <80% safe, >=80% and <100% warning, >=100% danger
_WARNING_PCT = 80.0


def _status_from_percentage(pct: float) -> Literal["safe", "warning", "danger"]:
    if pct >= 100.0:
        return "danger"
    if pct >= _WARNING_PCT:
        return "warning"
    return "safe"


def _spent_key(category: str, year: int, month: int) -> Tuple[str, int, int]:
    return (category, year, month)


class BudgetService:
    """CRUD for budgets and rolling comparison against actual expenses."""

    @staticmethod
    def _aggregate_spent_by_category_month(db: Session) -> Dict[Tuple[str, int, int], float]:
        """SUM(amount) GROUP BY category, calendar year, calendar month from expenses."""
        y = extract("year", Expense.date)
        m = extract("month", Expense.date)
        rows = (
            db.query(
                Expense.category,
                y.label("y"),
                m.label("m"),
                func.coalesce(func.sum(Expense.amount), 0.0),
            )
            .group_by(Expense.category, y, m)
            .all()
        )
        out: Dict[Tuple[str, int, int], float] = {}
        for r in rows:
            key = _spent_key(r.category, int(r.y), int(r.m))
            out[key] = round(float(r[3]), 2)
        return out

    @staticmethod
    def create(db: Session, data: BudgetCreate) -> Budget:
        row = Budget(
            id=str(uuid.uuid4()),
            category=data.category,
            amount=data.amount,
            month=data.month,
            year=data.year,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        logger.info("Created budget %s %s %d-%02d", row.id, row.category, row.year, row.month)
        return row

    @staticmethod
    def list_all(db: Session) -> List[Budget]:
        return (
            db.query(Budget)
            .order_by(Budget.year.desc(), Budget.month.desc(), Budget.category.asc())
            .all()
        )

    @staticmethod
    def get_by_id(db: Session, budget_id: str) -> Budget:
        row = db.query(Budget).filter(Budget.id == budget_id).first()
        if not row:
            raise BudgetNotFoundError(budget_id)
        return row

    @staticmethod
    def update(db: Session, budget_id: str, data: BudgetUpdate) -> Budget:
        row = BudgetService.get_by_id(db, budget_id)
        updates = data.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(row, field, value)
        db.commit()
        db.refresh(row)
        logger.info("Updated budget %s", budget_id)
        return row

    @staticmethod
    def delete(db: Session, budget_id: str) -> None:
        row = BudgetService.get_by_id(db, budget_id)
        db.delete(row)
        db.commit()
        logger.info("Deleted budget %s", budget_id)

    @staticmethod
    def build_status_list(db: Session) -> List[BudgetStatusResponse]:
        """
        For each budget, compare its amount to SUM(expenses) in the same
        category and calendar month/year (dynamic aggregation).
        """
        spent_map = BudgetService._aggregate_spent_by_category_month(db)
        budgets = BudgetService.list_all(db)
        result: List[BudgetStatusResponse] = []

        for b in budgets:
            spent = spent_map.get(_spent_key(b.category, b.year, b.month), 0.0)
            limit = round(float(b.amount), 2)
            remaining = round(limit - spent, 2)
            if limit > 0:
                pct = round((spent / limit) * 100.0, 2)
            else:
                pct = 100.0 if spent > 0 else 0.0

            result.append(
                BudgetStatusResponse(
                    id=b.id,
                    category=b.category,
                    month=b.month,
                    year=b.year,
                    budget=limit,
                    spent=spent,
                    remaining=remaining,
                    percentage_used=pct,
                    status=_status_from_percentage(pct),
                )
            )
        return result
