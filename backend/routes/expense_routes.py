"""
ValueTrack — Expense Routes
POST /api/expenses  — create single expense
GET  /api/expenses  — list expenses by user + optional month/year
"""
from flask import Blueprint, request, jsonify
from services.expense_service import create_single_expense, get_expenses

expense_bp = Blueprint('expenses', __name__, url_prefix='/api/expenses')


@expense_bp.route('', methods=['POST'])
def create_expense():
    """Create a single expense record."""
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'Request body is required'}), 400

    user_id = data.get('user_id')
    category = data.get('category', '')
    amount = data.get('amount')
    expense_date = data.get('expense_date', '')
    description = data.get('description', '')
    is_fixed = bool(data.get('is_fixed', False))

    if not user_id or amount is None:
        return jsonify({'status': 'error', 'message': 'Missing required fields: user_id, category, amount, expense_date'}), 400

    try:
        user_id = int(user_id)
        amount = float(amount)
    except (ValueError, TypeError):
        return jsonify({'status': 'error', 'message': 'Invalid field types'}), 400

    try:
        result = create_single_expense(user_id, category, amount, expense_date, description, is_fixed)
        return jsonify({'status': 'success', 'message': 'Expense created successfully', 'data': result}), 201
    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to create expense: {str(e)}'}), 500


@expense_bp.route('', methods=['GET'])
def list_expenses():
    """List expenses for a user, optionally filtered by month/year."""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': 'user_id query parameter is required'}), 400

    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({'status': 'error', 'message': 'user_id must be an integer'}), 400

    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)

    try:
        result = get_expenses(user_id, month=month, year=year)
        return jsonify({'status': 'success', 'message': 'Expenses fetched successfully', 'data': result}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to fetch expenses: {str(e)}'}), 500
