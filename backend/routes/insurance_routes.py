"""
ValueTrack — Insurance Routes
POST /api/insurance/request          — run scorer and persist results
GET  /api/insurance/result/<id>      — fetch persisted ranking
"""
from flask import Blueprint, request, jsonify
from services.insurance_service import score_insurance, get_results

insurance_bp = Blueprint('insurance', __name__, url_prefix='/api/insurance')


@insurance_bp.route('/request', methods=['POST'])
def create_request():
    """Score insurance plans and persist top 5 results."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    user_id = data.get('user_id')
    age = data.get('age')
    pre_existing = data.get('pre_existing_condition', False)
    budget = data.get('annual_budget')

    if not all([user_id, age is not None, budget is not None]):
        return jsonify({'error': 'Missing required fields: user_id, age, annual_budget'}), 400

    try:
        user_id = int(user_id)
        age = int(age)
        budget = float(budget)
        pre_existing = bool(pre_existing)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid field types'}), 400

    try:
        result = score_insurance(user_id, age, pre_existing, budget)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Scoring failed: {str(e)}'}), 500


@insurance_bp.route('/result/<int:request_id>', methods=['GET'])
def fetch_result(request_id):
    """Fetch persisted insurance ranking by request ID."""
    try:
        result = get_results(request_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f'Failed to fetch results: {str(e)}'}), 500
