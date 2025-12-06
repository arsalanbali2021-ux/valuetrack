"""
ValueTrack -- EMI Calculation Unit Tests
Three scenarios:
  1. Standard loan (8.5% interest, 12 months)
  2. Zero-interest loan
  3. Small principal with rounding edge case
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from decimal import Decimal
from datetime import date
from services.emi_service import calculate_emi, generate_schedule, _round2


def test_standard_loan():
    """
    Standard EMI: P=100000, rate=8.5%, tenure=12 months.
    Final remaining_balance must be exactly 0.00.
    """
    principal = Decimal('100000')
    rate = Decimal('8.5')
    tenure = 12
    start = date(2025, 1, 1)

    emi = calculate_emi(principal, rate, tenure)
    schedule = generate_schedule(principal, rate, tenure, start)

    # EMI should be positive and reasonable
    assert float(emi) > 8000 and float(emi) < 10000, f"EMI {emi} is not in expected range"

    # Schedule should have exactly 12 rows
    assert len(schedule) == 12, f"Expected 12 rows, got {len(schedule)}"

    # Final balance must be exactly 0.00
    last_row = schedule[-1]
    assert last_row['remaining_balance'] == Decimal('0.00'), \
        f"Final balance is {last_row['remaining_balance']}, expected 0.00"

    # All EMI amounts should be positive
    for row in schedule:
        assert row['emi_amount'] > 0, f"Month {row['month_no']}: EMI should be positive"
        assert row['principal_component'] >= 0, f"Month {row['month_no']}: principal should be >= 0"
        assert row['interest_component'] >= 0, f"Month {row['month_no']}: interest should be >= 0"

    print("[PASS] test_standard_loan")


def test_zero_interest():
    """
    Zero-interest: P=10000, rate=0%, tenure=4 months.
    Each EMI should be exactly 2500.00.
    """
    principal = Decimal('10000')
    rate = Decimal('0')
    tenure = 4
    start = date(2025, 6, 1)

    emi = calculate_emi(principal, rate, tenure)
    schedule = generate_schedule(principal, rate, tenure, start)

    assert emi == Decimal('2500.00'), f"Zero-interest EMI is {emi}, expected 2500.00"
    assert len(schedule) == 4

    for row in schedule:
        assert row['interest_component'] == Decimal('0.00'), \
            f"Month {row['month_no']}: interest should be 0 for zero-rate"

    # Final balance
    assert schedule[-1]['remaining_balance'] == Decimal('0.00')

    print("[PASS] test_zero_interest")


def test_rounding_edge_case():
    """
    Small principal with potential rounding drift.
    P=1000, rate=7.0%, tenure=3 months.
    """
    principal = Decimal('1000')
    rate = Decimal('7.0')
    tenure = 3
    start = date(2025, 3, 15)

    schedule = generate_schedule(principal, rate, tenure, start)

    assert len(schedule) == 3

    # Final balance must be exactly 0.00 regardless of rounding
    assert schedule[-1]['remaining_balance'] == Decimal('0.00'), \
        f"Final balance is {schedule[-1]['remaining_balance']}, expected 0.00"

    # Sum of principal_component should equal the original principal
    total_principal_paid = sum(row['principal_component'] for row in schedule)
    assert total_principal_paid == principal, \
        f"Total principal paid {total_principal_paid} != original {principal}"

    print("[PASS] test_rounding_edge_case")


if __name__ == '__main__':
    test_standard_loan()
    test_zero_interest()
    test_rounding_edge_case()
    print("\nAll EMI tests passed!")
