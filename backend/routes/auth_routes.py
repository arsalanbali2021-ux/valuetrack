"""
ValueTrack — Auth Routes
POST /api/auth/register
POST /api/auth/login
"""
from flask import Blueprint, request, jsonify
from services.auth_service import register_user, login_user

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    name = data.get('name', '')
    email = data.get('email', '')
    password = data.get('password', '')

    try:
        result = register_user(name, email, password)
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Registration failed'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return token."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    email = data.get('email', '')
    password = data.get('password', '')

    try:
        result = login_user(email, password)
        response = jsonify(result)
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
        return jsonify({'error': str(e)}), 401
    except Exception as e:
        return jsonify({'error': 'Login failed'}), 500
