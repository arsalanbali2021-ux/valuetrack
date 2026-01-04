"""
ValueTrack — Dashboard Routes
GET /api/dashboard?user_id=...  — aggregated financial overview
"""
from flask import Blueprint, request, jsonify
from sqlalchemy import func as sql_func
from datetime import date, datetime
from models import Loan, EMISchedule, Expense, InsuranceResult, InsuranceRequest, Insurance
from db import db_session

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


@dashboard_bp.route('', methods=['GET'])
def get_dashboard():
    """Return aggregated dashboard data for a user."""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id query parameter is required'}), 400

    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({'error': 'user_id must be an integer'}), 400

    today = date.today()

    # --- Total loans count ---
    total_loans = db_session.query(sql_func.count(Loan.loan_id)).filter(
        Loan.user_id == user_id
    ).scalar() or 0

    # --- Total outstanding principal (sum of remaining_balance of last EMI row per loan) ---
    # Get all loan IDs for this user
    loan_ids = [lid for (lid,) in db_session.query(Loan.loan_id).filter(
        Loan.user_id == user_id
    ).all()]

    total_outstanding = 0.0
    if loan_ids:
        # For each loan, get the latest EMI row's remaining_balance
        for lid in loan_ids:
            last_emi = db_session.query(EMISchedule).filter(
                EMISchedule.loan_id == lid
            ).order_by(EMISchedule.month_no.desc()).first()
            if last_emi:
                # Find the last unpaid month (where due_date >= today)
                unpaid = db_session.query(EMISchedule).filter(
                    EMISchedule.loan_id == lid,
                    EMISchedule.due_date >= today
                ).order_by(EMISchedule.month_no.asc()).first()
                if unpaid:
                    total_outstanding += float(unpaid.remaining_balance)

    total_outstanding = round(total_outstanding, 2)

    # --- Monthly expenses (current month) ---
    monthly_expenses = db_session.query(
        sql_func.coalesce(sql_func.sum(Expense.amount), 0)
    ).filter(
        Expense.user_id == user_id,
        sql_func.extract('month', Expense.expense_date) == today.month,
        sql_func.extract('year', Expense.expense_date) == today.year
    ).scalar()
    monthly_expenses = round(float(monthly_expenses), 2)

    # --- Next upcoming EMI ---
    next_emi_data = None
    if loan_ids:
        next_emi = db_session.query(EMISchedule).filter(
            EMISchedule.loan_id.in_(loan_ids),
            EMISchedule.due_date >= today
        ).order_by(EMISchedule.due_date.asc()).first()

        if next_emi:
            next_emi_data = {
                'loan_id': next_emi.loan_id,
                'due_date': str(next_emi.due_date),
                'amount': float(next_emi.emi_amount)
            }

    # --- Top insurance result (most recent request) ---
    top_insurance_data = None
    latest_request = db_session.query(InsuranceRequest).filter(
        InsuranceRequest.user_id == user_id
    ).order_by(InsuranceRequest.created_at.desc()).first()

    if latest_request:
        top_result = db_session.query(InsuranceResult).filter(
            InsuranceResult.request_id == latest_request.request_id,
            InsuranceResult.rank_position == 1
        ).first()

        if top_result:
            policy = db_session.query(Insurance).filter(
                Insurance.insurance_id == top_result.insurance_id
            ).first()
            if policy:
                top_insurance_data = {
                    'insurance_id': top_result.insurance_id,
                    'provider': policy.provider_name,
                    'rank_score': float(top_result.rank_score)
                }

    return jsonify({
        'total_loans': total_loans,
        'total_outstanding_principal': total_outstanding,
        'monthly_expenses': monthly_expenses,
        'next_emi': next_emi_data,
        'top_insurance': top_insurance_data
    }), 200
