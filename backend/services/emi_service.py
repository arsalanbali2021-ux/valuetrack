"""
ValueTrack — EMI Calculation Service
Uses Python Decimal for precision. Follows deterministic rounding rules.

Algorithm:
  r = annual_interest_rate / 100 / 12  (monthly rate)
  If r == 0:  EMI = P / N
  Else:       EMI = P * r * (1+r)^N / ((1+r)^N - 1)
  Last month adjusted so remaining_balance == 0.00.
"""
from decimal import Decimal, ROUND_HALF_UP, getcontext
from datetime import date
from dateutil.relativedelta import relativedelta
from models import Loan, EMISchedule
from db import db_session

# Set high precision for intermediate calculations
getcontext().prec = 28

# Shortcut for rounding to 2 decimal places
TWO_PLACES = Decimal('0.01')


def _round2(value: Decimal) -> Decimal:
    """Round a Decimal to 2 decimal places using ROUND_HALF_UP."""
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def calculate_emi(principal: Decimal, annual_rate: Decimal, tenure: int) -> Decimal:
    """
    Calculate monthly EMI amount.
    principal: loan amount
    annual_rate: annual interest rate as percentage (e.g., 7.5)
    tenure: number of months
    """
    if tenure <= 0:
        raise ValueError("Tenure must be positive")
    if principal <= 0:
        raise ValueError("Principal must be positive")

    r = annual_rate / Decimal('100') / Decimal('12')

    if r == 0:
        # Zero interest: simple division
        return _round2(principal / Decimal(tenure))
    else:
        # Standard EMI formula: P * r * (1+r)^N / ((1+r)^N - 1)
        one_plus_r_n = (Decimal('1') + r) ** tenure
        emi = principal * r * one_plus_r_n / (one_plus_r_n - Decimal('1'))
        return _round2(emi)


def generate_schedule(principal: Decimal, annual_rate: Decimal,
                      tenure: int, start: date) -> list:
    """
    Generate the full amortization schedule as a list of dicts.
    Guarantees final remaining_balance == 0.00.
    """
    emi = calculate_emi(principal, annual_rate, tenure)
    r = annual_rate / Decimal('100') / Decimal('12')

    schedule = []
    remaining = _round2(principal)

    for month in range(1, tenure + 1):
        due_date = start + relativedelta(months=month)

        if month == tenure:
            # Last month: adjust to zero out balance
            interest = _round2(remaining * r)
            principal_payment = remaining
            emi_this_month = _round2(principal_payment + interest)
            remaining_after = Decimal('0.00')
        else:
            interest = _round2(remaining * r)
            principal_payment = _round2(emi - interest)
            remaining_after = _round2(remaining - principal_payment)
            emi_this_month = emi

        schedule.append({
            'month_no': month,
            'emi_amount': emi_this_month,
            'principal_component': principal_payment,
            'interest_component': interest,
            'remaining_balance': remaining_after,
            'due_date': due_date
        })

        remaining = remaining_after

    return schedule


def create_loan_with_schedule(user_id: int, principal: float,
                               annual_interest_rate: float,
                               tenure_months: int,
                               start_date_str: str) -> dict:
    """
    Create a loan record and persist its EMI schedule.
    Returns dict with loan_id, emi amount, and created_at.
    """
    # Convert to Decimal for precision
    p = Decimal(str(principal))
    rate = Decimal(str(annual_interest_rate))
    start = date.fromisoformat(start_date_str)

    # Validate
    if p <= 0:
        raise ValueError("Principal must be positive")
    if rate < 0:
        raise ValueError("Interest rate cannot be negative")
    if tenure_months <= 0:
        raise ValueError("Tenure must be positive")

    # Create loan record
    loan = Loan(
        user_id=user_id,
        principal=float(p),
        annual_interest_rate=float(rate),
        tenure_months=tenure_months,
        start_date=start
    )
    db_session.add(loan)
    db_session.flush()  # get loan_id

    # Generate and insert schedule
    schedule = generate_schedule(p, rate, tenure_months, start)
    emi_amount = None

    for row in schedule:
        emi_row = EMISchedule(
            loan_id=loan.loan_id,
            month_no=row['month_no'],
            emi_amount=float(row['emi_amount']),
            principal_component=float(row['principal_component']),
            interest_component=float(row['interest_component']),
            remaining_balance=float(row['remaining_balance']),
            due_date=row['due_date']
        )
        db_session.add(emi_row)
        if emi_amount is None:
            emi_amount = float(row['emi_amount'])

    db_session.commit()
    db_session.refresh(loan)

    return {
        'loan_id': loan.loan_id,
        'emi': emi_amount,
        'created_at': str(loan.created_at)
    }
