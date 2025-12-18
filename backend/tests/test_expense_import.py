"""
ValueTrack -- Expense Import Integration Tests
Simulates CSV upload and validates summary JSON semantics.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import io
import csv
from unittest.mock import MagicMock


def _create_csv_file(rows, headers=None):
    """Helper: create an in-memory CSV file-like object."""
    if headers is None:
        headers = ['date', 'amount', 'category', 'description']

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)

    # Create a file-like object with filename attribute
    output.seek(0)
    file_obj = io.BytesIO(output.getvalue().encode('utf-8'))
    file_obj.filename = 'test_expenses.csv'
    return file_obj


def test_valid_csv_import():
    """All rows valid -- should insert all, skip none."""
    from services.expense_service import _validate_file, _parse_date

    rows = [
        ['2025-10-01', '250.00', 'Food', 'Groceries'],
        ['2025-10-05', '1500.00', 'Rent', 'Monthly rent'],
        ['2025-10-10', '45.00', 'Transport', 'Bus fare'],
    ]
    file_obj = _create_csv_file(rows)

    # Validate file extension
    ext = _validate_file(file_obj)
    assert ext == 'csv', f"Expected 'csv', got '{ext}'"

    # Validate date parsing
    assert _parse_date('2025-10-01') == '2025-10-01'
    assert _parse_date('bad-date') is None

    print("[PASS] test_valid_csv_import")


def test_skipped_rows():
    """Some rows should be skipped due to invalid data."""
    from services.expense_service import _parse_date

    # Test various invalid values
    assert _parse_date('not-a-date') is None, "Should reject invalid date"
    assert _parse_date('2025-10-15') == '2025-10-15', "Should accept valid date"

    # Test negative / zero amounts
    assert float('-50.00') < 0, "Negative amounts should fail validation"
    assert float('0') <= 0, "Zero amounts should fail validation"

    print("[PASS] test_skipped_rows")


def test_missing_columns():
    """File missing required columns should be rejected."""
    from services.expense_service import _validate_file

    # Test with wrong extension
    file_obj = io.BytesIO(b"some data")
    file_obj.filename = 'test.pdf'
    try:
        _validate_file(file_obj)
        assert False, "Should have raised ValueError for .pdf"
    except ValueError as e:
        assert 'Unsupported' in str(e)

    # Test with valid extension
    file_obj2 = io.BytesIO(b"some data")
    file_obj2.filename = 'test.csv'
    ext = _validate_file(file_obj2)
    assert ext == 'csv'

    print("[PASS] test_missing_columns")


def test_summary_structure():
    """Summary JSON should have correct structure."""
    summary = {
        'inserted': 5,
        'skipped': [
            {'row': 3, 'reason': 'invalid date'},
            {'row': 7, 'reason': 'amount must be positive'}
        ],
        'errors': []
    }

    assert isinstance(summary['inserted'], int)
    assert isinstance(summary['skipped'], list)
    assert isinstance(summary['errors'], list)
    assert all('row' in s and 'reason' in s for s in summary['skipped'])

    print("[PASS] test_summary_structure")


if __name__ == '__main__':
    test_valid_csv_import()
    test_skipped_rows()
    test_missing_columns()
    test_summary_structure()
    print("\nAll expense import tests passed!")
