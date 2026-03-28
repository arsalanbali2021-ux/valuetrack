"""
ValueTrack — Loan Routes
POST /api/loans          — create loan + EMI schedule
GET  /api/loans/<id>/schedule — get EMI schedule
"""
from flask import Blueprint, request, jsonify
from services.emi_service import create_loan_with_schedule
from models import Loan, EMISchedule
from db import db_session

loan_bp = Blueprint('loans', __name__, url_prefix='/api/loans')


@loan_bp.route('', methods=['POST'])
def create_loan():
    """Create a new loan and generate its EMI schedule."""
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'Request body is required'}), 400

    # Required fields
    user_id = data.get('user_id')
    principal = data.get('principal')
    annual_interest_rate = data.get('annual_interest_rate')
    tenure_months = data.get('tenure_months')
    start_date = data.get('start_date')

    # Validate presence
    if not all([user_id, principal is not None, annual_interest_rate is not None,
                tenure_months, start_date]):
        return jsonify({'status': 'error', 'message': 'Missing required fields: user_id, principal, '
                                 'annual_interest_rate, tenure_months, start_date'}), 400

    # Type validation
    try:
        user_id = int(user_id)
        principal = float(principal)
        annual_interest_rate = float(annual_interest_rate)
        tenure_months = int(tenure_months)
    except (ValueError, TypeError):
        return jsonify({'status': 'error', 'message': 'Invalid field types'}), 400

    try:
        result = create_loan_with_schedule(
            user_id, principal, annual_interest_rate, tenure_months, start_date
        )
        return jsonify({'status': 'success', 'message': 'Loan created successfully', 'data': result}), 201
    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to create loan: {str(e)}'}), 500


@loan_bp.route('/<int:loan_id>/schedule', methods=['GET'])
def get_schedule(loan_id):
    """Return the EMI schedule for a given loan."""
    loan = db_session.query(Loan).filter(Loan.loan_id == loan_id).first()
    if not loan:
        return jsonify({'status': 'error', 'message': 'Loan not found'}), 404

    rows = db_session.query(EMISchedule).filter(
        EMISchedule.loan_id == loan_id
    ).order_by(EMISchedule.month_no).all()

    return jsonify({
        'status': 'success',
        'message': 'Schedule loaded accurately',
        'data': {
            'loan_id': loan_id,
            'loan': loan.to_dict(),
            'schedule': [r.to_dict() for r in rows]
        }
    }), 200
