"""
ValueTrack — Expense Service
Create and list expenses for a user.
"""
from datetime import datetime
from models import Expense
from db import db_session


def create_single_expense(user_id: int, category: str, amount: float,
                           expense_date: str, description: str = '', is_fixed: bool = False) -> dict:
    """Create a single expense record."""
    if not category or not category.strip():
        raise ValueError("Category is required")
    if amount <= 0:
        raise ValueError("Amount must be positive")

    try:
        parsed_date = datetime.strptime(expense_date, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        raise ValueError("Invalid date format. Use YYYY-MM-DD")

    expense = Expense(
        user_id=user_id,
        category=category.strip(),
        amount=amount,
        expense_date=parsed_date,
        description=description.strip() if description else '',
        is_fixed=int(is_fixed)
    )
    db_session.add(expense)
    db_session.commit()
    db_session.refresh(expense)

    return expense.to_dict()


def get_expenses(user_id: int, month: int = None, year: int = None) -> dict:
    """
    Get expenses for a user, optionally filtered by month/year.
    Returns list of expenses and total.
    """
    from sqlalchemy import extract

    query = db_session.query(Expense).filter(Expense.user_id == user_id)

    if year:
        query = query.filter(extract('year', Expense.expense_date) == year)
    if month:
        query = query.filter(extract('month', Expense.expense_date) == month)

    expenses = query.order_by(Expense.expense_date.desc()).all()

    total = sum(float(e.amount) for e in expenses)

    return {
        'expenses': [e.to_dict() for e in expenses],
        'total': round(total, 2),
        'count': len(expenses)
    }
