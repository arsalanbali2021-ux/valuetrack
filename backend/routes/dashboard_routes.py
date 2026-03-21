"""
ValueTrack — Dashboard Routes
GET /api/dashboard?user_id=...  — aggregated financial overview + chart data
"""
from flask import Blueprint, request, jsonify
from sqlalchemy import func as sql_func
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from models import Loan, EMISchedule, Expense, InsuranceResult, InsuranceRequest, Insurance, User
from db import db_session

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


@dashboard_bp.route('', methods=['GET'])
def get_dashboard():
    """Return aggregated dashboard data for a user."""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': 'user_id query parameter is required'}), 400

    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({'status': 'error', 'message': 'user_id must be an integer'}), 400

    today = date.today()

    user = db_session.query(User).filter(User.user_id == user_id).first()
    if not user:
        return jsonify({'status': 'error', 'message': 'User not found'}), 404

    monthly_budget = float(user.monthly_budget)

    # --- Metrics ---
    total_loans = db_session.query(sql_func.count(Loan.loan_id)).filter(
        Loan.user_id == user_id
    ).scalar() or 0

    loan_ids = [lid for (lid,) in db_session.query(Loan.loan_id).filter(
        Loan.user_id == user_id
    ).all()]

    total_outstanding = 0.0
    if loan_ids:
        for lid in loan_ids:
            unpaid = db_session.query(EMISchedule).filter(
                EMISchedule.loan_id == lid,
                EMISchedule.due_date >= today
            ).order_by(EMISchedule.month_no.asc()).first()
            if unpaid:
                total_outstanding += float(unpaid.remaining_balance)

    total_outstanding = round(total_outstanding, 2)

    monthly_expenses = db_session.query(
        sql_func.coalesce(sql_func.sum(Expense.amount), 0)
    ).filter(
        Expense.user_id == user_id,
        sql_func.extract('month', Expense.expense_date) == today.month,
        sql_func.extract('year', Expense.expense_date) == today.year
    ).scalar()
    monthly_expenses = round(float(monthly_expenses), 2)

    # Fetch 5 most recent expenses
    recent_expenses_query = db_session.query(Expense).filter(
        Expense.user_id == user_id
    ).order_by(Expense.expense_date.desc(), Expense.expense_id.desc()).limit(5).all()

    recent_activity = [{
        'date': str(exp.expense_date),
        'description': exp.description,
        'category': exp.category,
        'amount': float(exp.amount),
        'is_fixed': bool(exp.is_fixed)
    } for exp in recent_expenses_query]

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
                    'plan_name': policy.plan_name,
                    'type': policy.plan_type,
                    'rank_score': float(top_result.rank_score)
                }

    # --- Chart Data (Expense Distribution - current year) ---
    expense_dist = db_session.query(
        Expense.category, sql_func.sum(Expense.amount)
    ).filter(
        Expense.user_id == user_id,
        sql_func.extract('year', Expense.expense_date) == today.year
    ).group_by(Expense.category).all()
    expense_distribution = [{'category': cat, 'total': float(tot)} for cat, tot in expense_dist]

    # --- Chart Data (Monthly Expense Trend - Last 6 Months) ---
    six_months_ago = today - relativedelta(months=5)
    monthly_trend = db_session.query(
        sql_func.extract('month', Expense.expense_date).label('m'),
        sql_func.extract('year', Expense.expense_date).label('y'),
        sql_func.sum(Expense.amount)
    ).filter(
        Expense.user_id == user_id,
        Expense.expense_date >= date(six_months_ago.year, six_months_ago.month, 1)
    ).group_by('y', 'm').order_by('y', 'm').all()
    
    # Fill in blanks for the last 6 months to ensure chart continuity
    expense_trend = []
    for i in range(5, -1, -1):
        dt = today - relativedelta(months=i)
        val = next((float(tot) for m, y, tot in monthly_trend if int(m) == dt.month and int(y) == dt.year), 0.0)
        expense_trend.append({
            'label': dt.strftime('%b'),
            'total': val
        })

    # --- Chart Data (Loan Balance Trend - Next 6 Months) ---
    loan_trend = []
    if loan_ids:
        for i in range(6):
            dt = today + relativedelta(months=i)
            # End of the month approximation
            eom = date(dt.year, dt.month, 1) + relativedelta(months=1) - relativedelta(days=1)
            
            # Find the remaining balance for all active loans on that date
            # We look for the EMI schedule entry that is closest but before or equal to EOM
            month_balance = 0.0
            for lid in loan_ids:
                closest_emi = db_session.query(EMISchedule).filter(
                    EMISchedule.loan_id == lid,
                    EMISchedule.due_date >= eom
                ).order_by(EMISchedule.due_date.asc()).first()
                if closest_emi:
                    month_balance += float(closest_emi.remaining_balance)
                else:
                    # Loan will be fully paid off by then, or hasn't started
                    pass
            loan_trend.append({
                'label': dt.strftime('%b %Y'),
                'balance': round(month_balance, 2)
            })

    return jsonify({
        'status': 'success',
        'message': 'Dashboard data loaded',
        'data': {
            'total_loans': total_loans,
            'total_outstanding_principal': total_outstanding,
            'monthly_expenses': monthly_expenses,
            'monthly_budget': monthly_budget,
            'recent_activity': recent_activity,
            'next_emi': next_emi_data,
            'top_insurance': top_insurance_data,
            'charts': {
                'expense_distribution': expense_distribution,
                'expense_trend': expense_trend,
                'loan_trend': loan_trend
            }
        }
    }), 200
