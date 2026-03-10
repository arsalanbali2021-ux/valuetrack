"""
ValueTrack — Auth Routes
POST /api/auth/register
POST /api/auth/login
"""
import traceback
from flask import Blueprint, request, jsonify
from services.auth_service import register_user, login_user, update_budget

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'Request body is required'}), 400

    name = data.get('name', '')
    email = data.get('email', '')
    password = data.get('password', '')

    try:
        result = register_user(name, email, password)
        return jsonify({
            'status': 'success',
            'message': 'Registration successful',
            'data': result
        }), 201
    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': 'An internal server error occurred'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return token."""
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'Request body is required'}), 400

    email = data.get('email', '')
    password = data.get('password', '')

    try:
        result = login_user(email, password)
        response = jsonify({
            'status': 'success',
            'message': 'Login successful',
            'data': result
        })
        # Set HTTP-only cookie for academic scope
        response.set_cookie(
            'auth_token',
            result['token'],
            httponly=True,
            samesite='Lax',
            max_age=86400  # 24 hours
        )
        return response, 200
    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 401
    except Exception as e:
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': 'An internal server error occurred'}), 500


@auth_bp.route('/budget', methods=['PUT'])
def set_budget():
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'Request body is required'}), 400

    user_id = data.get('user_id')
    budget = data.get('monthly_budget')

    if not user_id or budget is None:
        return jsonify({'status': 'error', 'message': 'user_id and monthly_budget required'}), 400

    try:
        user_id = int(user_id)
        budget = float(budget)
        update_budget(user_id, budget)
        return jsonify({'status': 'success', 'message': 'Budget updated successfully'}), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 400
