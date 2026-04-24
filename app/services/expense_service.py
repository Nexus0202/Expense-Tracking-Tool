import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.schemas.common import CategorySummary, DashboardSummary, MonthlySummary
from app.schemas.expense import ExpenseCreate, ExpenseUpdate
from app.utils.exceptions import ExpenseNotFoundError

logger = logging.getLogger(__name__)


class ExpenseService:
    """Business-logic layer for expense CRUD and analytics."""

    @staticmethod
    def create(db: Session, data: ExpenseCreate) -> Expense:
        """Insert a new expense record."""
        expense = Expense(
            id=str(uuid.uuid4()),
            amount=data.amount,
            category=data.category,
            description=data.description or "",
            date=data.date,
            source=data.source,
        )
        db.add(expense)
        db.commit()
        db.refresh(expense)
        logger.info("Created expense %s (%.2f %s)", expense.id, expense.amount, expense.category)
        return expense

    @staticmethod
    def get_by_id(db: Session, expense_id: str) -> Expense:
        """Fetch a single expense or raise 404."""
        expense = db.query(Expense).filter(Expense.id == expense_id).first()
        if not expense:
            raise ExpenseNotFoundError(expense_id)
        return expense

    @staticmethod
    def get_all(
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Expense], int]:
        """Return paginated expenses with optional filters."""
        query = db.query(Expense)

        if start_date:
            query = query.filter(Expense.date >= start_date)
        if end_date:
            query = query.filter(Expense.date <= end_date)
        if category:
            query = query.filter(Expense.category.ilike(f"%{category}%"))

        total = query.count()
        items = (
            query.order_by(Expense.date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    @staticmethod
    def update(db: Session, expense_id: str, data: ExpenseUpdate) -> Expense:
        """Partially update an expense (only fields provided in the request)."""
        expense = ExpenseService.get_by_id(db, expense_id)
        updates = data.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(expense, field, value)
        expense.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(expense)
        logger.info("Updated expense %s", expense_id)
        return expense

    @staticmethod
    def delete(db: Session, expense_id: str) -> None:
        """Hard-delete an expense."""
        expense = ExpenseService.get_by_id(db, expense_id)
        db.delete(expense)
        db.commit()
        logger.info("Deleted expense %s", expense_id)

    @staticmethod
    def get_summary(
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> DashboardSummary:
        """Aggregate totals by category and month."""
        query = db.query(Expense)
        if start_date:
            query = query.filter(Expense.date >= start_date)
        if end_date:
            query = query.filter(Expense.date <= end_date)

        totals = query.with_entities(
            func.sum(Expense.amount), func.count(Expense.id)
        ).first()
        total_amount: float = totals[0] or 0.0
        total_count: int = totals[1] or 0

        category_rows = (
            query.with_entities(
                Expense.category,
                func.sum(Expense.amount).label("total"),
                func.count(Expense.id).label("count"),
            )
            .group_by(Expense.category)
            .order_by(func.sum(Expense.amount).desc())
            .all()
        )
        by_category = [
            CategorySummary(category=r.category, total=round(r.total, 2), count=r.count)
            for r in category_rows
        ]

        month_rows = (
            query.with_entities(
                extract("year", Expense.date).label("year"),
                extract("month", Expense.date).label("month"),
                func.sum(Expense.amount).label("total"),
                func.count(Expense.id).label("count"),
            )
            .group_by("year", "month")
            .order_by("year", "month")
            .all()
        )
        by_month = [
            MonthlySummary(
                year=int(r.year), month=int(r.month), total=round(r.total, 2), count=r.count
            )
            for r in month_rows
        ]

        return DashboardSummary(
            total_expenses=round(total_amount, 2),
            total_count=total_count,
            by_category=by_category,
            by_month=by_month,
        )

    @staticmethod
    def bulk_create(db: Session, expenses_data: List[dict]) -> List[Expense]:
        """Bulk-insert expenses parsed from a PDF (source = 'pdf')."""
        created: List[Expense] = []
        for item in expenses_data:
            raw_date = item["date"]
            date = (
                datetime.strptime(raw_date, "%Y-%m-%d")
                if isinstance(raw_date, str)
                else raw_date
            )
            expense = Expense(
                id=str(uuid.uuid4()),
                amount=item["amount"],
                category=item["category"],
                description=item.get("description", ""),
                date=date,
                source="pdf",
            )
            db.add(expense)
            created.append(expense)

        db.commit()
        for exp in created:
            db.refresh(exp)
        logger.info("Bulk-created %d expenses from PDF", len(created))
        return created
