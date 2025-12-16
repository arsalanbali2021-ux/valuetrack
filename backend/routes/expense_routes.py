"""
ValueTrack — Expense Routes
POST /api/expenses         — create single expense
POST /api/expenses/import  — file upload (CSV/XLSX)
GET  /api/expenses         — list expenses by user + optional month/year
"""
from flask import Blueprint, request, jsonify
from services.expense_service import (
    create_single_expense, import_expenses, get_expenses
)

expense_bp = Blueprint('expenses', __name__, url_prefix='/api/expenses')


@expense_bp.route('', methods=['POST'])
def create_expense():
    """Create a single expense record."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    user_id = data.get('user_id')
    category = data.get('category', '')
    amount = data.get('amount')
    expense_date = data.get('expense_date', '')
    description = data.get('description', '')

    if not user_id or amount is None:
        return jsonify({'error': 'Missing required fields: user_id, category, amount, expense_date'}), 400

    try:
        user_id = int(user_id)
        amount = float(amount)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid field types'}), 400

    try:
        result = create_single_expense(user_id, category, amount, expense_date, description)
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to create expense: {str(e)}'}), 500


@expense_bp.route('/import', methods=['POST'])
def import_file():
    """Import expenses from CSV/XLSX file."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided. Use multipart form field "file".'}), 400

    file_obj = request.files['file']
    if not file_obj.filename:
        return jsonify({'error': 'Empty filename'}), 400

    user_id = request.form.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required (form field)'}), 400

    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({'error': 'user_id must be an integer'}), 400

    try:
        result = import_expenses(user_id, file_obj)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Import failed: {str(e)}'}), 500


@expense_bp.route('', methods=['GET'])
def list_expenses():
    """List expenses for a user, optionally filtered by month/year."""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id query parameter is required'}), 400

    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({'error': 'user_id must be an integer'}), 400

    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)

    try:
        result = get_expenses(user_id, month=month, year=year)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': f'Failed to fetch expenses: {str(e)}'}), 500
