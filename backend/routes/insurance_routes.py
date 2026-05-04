"""
ValueTrack — Insurance Routes
POST /api/insurance/request          — run scorer and persist results (source: all | irdai)
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
        return jsonify({'status': 'error', 'message': 'Request body is required'}), 400

    user_id = data.get('user_id')
    age = data.get('age')
    needs_critical_illness = data.get('needs_critical_illness', False)
    needs_maternity = data.get('needs_maternity', False)
    needs_accident = data.get('needs_accident', False)
    monthly_budget = data.get('monthly_budget')
    source = str(data.get('source') or 'all')

    if not all([user_id, age is not None, monthly_budget is not None]):
        return jsonify({'status': 'error', 'message': 'Missing required fields: user_id, age, monthly_budget'}), 400

    try:
        user_id = int(user_id)
        age = int(age)
        monthly_budget = float(monthly_budget)
        needs_critical_illness = bool(needs_critical_illness)
        needs_maternity = bool(needs_maternity)
        needs_accident = bool(needs_accident)
    except (ValueError, TypeError):
        return jsonify({'status': 'error', 'message': 'Invalid field types'}), 400

    try:
        result = score_insurance(user_id, age, needs_critical_illness, needs_maternity, needs_accident,
                                 monthly_budget, source)
        return jsonify({'status': 'success', 'message': 'Insurance scoring completed', 'data': result}), 200
    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Scoring failed: {str(e)}'}), 500


@insurance_bp.route('/result/<int:request_id>', methods=['GET'])
def fetch_result(request_id):
    """Fetch persisted insurance ranking by request ID."""
    try:
        result = get_results(request_id)
        return jsonify({'status': 'success', 'message': 'Results fetched', 'data': result}), 200
    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to fetch results: {str(e)}'}), 500
