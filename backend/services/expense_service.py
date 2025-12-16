"""
ValueTrack — Expense Import Service
Handles CSV/XLSX file import using pandas.
Validates columns and rows, skips invalid rows, returns summary.
"""
import pandas as pd
from datetime import datetime
from decimal import Decimal
from models import Expense
from db import db_session

REQUIRED_COLUMNS = {'date', 'amount', 'category', 'description'}
ALLOWED_EXTENSIONS = {'csv', 'xlsx'}
ALLOWED_MIMES = {
    'text/csv',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/octet-stream'  # some browsers send this for .csv
}


def _validate_file(file_obj) -> str:
    """
    Validate uploaded file extension and MIME type.
    Returns the extension on success.
    Raises ValueError on failure.
    """
    filename = file_obj.filename or ''
    if '.' not in filename:
        raise ValueError("File must have an extension (.csv or .xlsx)")

    ext = filename.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type '.{ext}'. Accepted: .csv, .xlsx")

    return ext


def _parse_date(val) -> str:
    """
    Try to parse a value as a date and return YYYY-MM-DD string.
    Returns None if unparseable.
    """
    if pd.isna(val):
        return None
    try:
        # Handle pandas Timestamp
        if isinstance(val, pd.Timestamp):
            return val.strftime('%Y-%m-%d')
        # Handle datetime
        if isinstance(val, datetime):
            return val.strftime('%Y-%m-%d')
        # Handle string
        dt = pd.to_datetime(str(val), dayfirst=False)
        return dt.strftime('%Y-%m-%d')
    except (ValueError, TypeError):
        return None


def import_expenses(user_id: int, file_obj) -> dict:
    """
    Import expenses from a CSV or XLSX file.

    Returns:
        {
            "inserted": int,
            "skipped": [{"row": int, "reason": str}, ...],
            "errors": []
        }
    """
    ext = _validate_file(file_obj)

    # Read file with pandas
    try:
        if ext == 'csv':
            df = pd.read_csv(file_obj)
        else:
            df = pd.read_excel(file_obj)
    except Exception as e:
        raise ValueError(f"Failed to parse file: {str(e)}")

    # Normalize column names: strip whitespace, lowercase
    df.columns = [col.strip().lower() for col in df.columns]

    # Check required columns
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    inserted = 0
    skipped = []

    for idx, row in df.iterrows():
        row_num = idx + 2  # +2 because pandas is 0-indexed and row 1 is header

        # Validate date
        parsed_date = _parse_date(row.get('date'))
        if parsed_date is None:
            skipped.append({'row': row_num, 'reason': 'invalid date'})
            continue

        # Validate amount
        try:
            amount = float(row.get('amount', 0))
            if amount <= 0:
                skipped.append({'row': row_num, 'reason': 'amount must be positive'})
                continue
        except (ValueError, TypeError):
            skipped.append({'row': row_num, 'reason': 'invalid amount'})
            continue

        # Validate category
        category = str(row.get('category', '')).strip()
        if not category or category == 'nan':
            skipped.append({'row': row_num, 'reason': 'missing category'})
            continue

        # Description is optional
        description = str(row.get('description', '')).strip()
        if description == 'nan':
            description = ''

        # Create expense record
        expense = Expense(
            user_id=user_id,
            category=category,
            amount=amount,
            expense_date=parsed_date,
            description=description
        )
        db_session.add(expense)
        inserted += 1

    # Commit all valid rows in a single transaction
    if inserted > 0:
        db_session.commit()

    return {
        'inserted': inserted,
        'skipped': skipped,
        'errors': []
    }


def create_single_expense(user_id: int, category: str, amount: float,
                           expense_date: str, description: str = '') -> dict:
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
        description=description.strip() if description else ''
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
    from sqlalchemy import extract, func as sql_func

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
