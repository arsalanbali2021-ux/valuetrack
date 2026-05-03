"""
ValueTrack — Admin Routes
CRUD for insurance plans, system settings, and expense categories,
plus the IRDAI product catalogue import.
All routes require admin role.
"""
import traceback
from flask import Blueprint, request, jsonify
from models import User, Insurance, SystemSetting, ExpenseCategory, IrdaiProduct
from services.irdai_import import import_products
from db import db_session

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


def _require_admin():
    """
    Validate that the requesting user is an admin.
    """
    user_id = request.args.get('user_id')
    if not user_id and request.is_json:
        user_id = request.get_json(silent=True, force=True)
        if isinstance(user_id, dict):
            user_id = user_id.get('user_id')

    if not user_id:
        return None, (jsonify({'status': 'error', 'message': 'user_id is required'}), 400)

    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return None, (jsonify({'status': 'error', 'message': 'Invalid user_id'}), 400)

    user = db_session.query(User).filter(User.user_id == user_id).first()
    if not user:
        return None, (jsonify({'status': 'error', 'message': 'User not found'}), 404)

    if user.role != 'admin':
        return None, (jsonify({'status': 'error', 'message': 'Access denied. Admin role required.'}), 403)

    return user, None


def _clean_uin(value):
    """Empty -> None. Otherwise the UIN must already be in the IRDAI catalogue."""
    uin = ''.join(str(value or '').split()).upper()
    if not uin:
        return None
    if not db_session.query(IrdaiProduct).filter(IrdaiProduct.uin == uin).first():
        raise ValueError(f'UIN {uin} is not in the IRDAI catalogue. Import the IRDAI list first.')
    return uin


# =====================================================================
# INSURANCE CRUD
# =====================================================================

@admin_bp.route('/insurance', methods=['GET'])
def list_insurance():
    _, error = _require_admin()
    if error: return error

    plans = db_session.query(Insurance).order_by(Insurance.insurance_id).all()
    return jsonify({'status': 'success', 'message': 'Fetched plans', 'data': [p.to_dict() for p in plans]}), 200


@admin_bp.route('/insurance', methods=['POST'])
def create_insurance():
    _, error = _require_admin()
    if error: return error

    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'Request body is required'}), 400

    required = ['plan_name', 'plan_type', 'min_age', 'max_age', 'monthly_premium', 'coverage_amount']
    for field in required:
        if field not in data or data[field] is None:
            return jsonify({'status': 'error', 'message': f'Missing required field: {field}'}), 400

    try:
        plan = Insurance(
            plan_name=str(data['plan_name']).strip(),
            plan_type=str(data['plan_type']).strip(),
            min_age=int(data['min_age']),
            max_age=int(data['max_age']),
            coverage_amount=float(data['coverage_amount']),
            has_critical_illness=1 if data.get('has_critical_illness') else 0,
            has_maternity=1 if data.get('has_maternity') else 0,
            has_accident=1 if data.get('has_accident') else 0,
            co_pay_percentage=int(data.get('co_pay_percentage', 0)),
            monthly_premium=float(data['monthly_premium']),
            irdai_uin=_clean_uin(data.get('irdai_uin'))
        )
        db_session.add(plan)
        db_session.commit()
        db_session.refresh(plan)
        return jsonify({'status': 'success', 'message': 'Plan created', 'data': plan.to_dict()}), 201
    except Exception as e:
        db_session.rollback()
        return jsonify({'status': 'error', 'message': f'Failed to create plan: {str(e)}'}), 400


@admin_bp.route('/insurance/<int:plan_id>', methods=['PUT'])
def update_insurance(plan_id):
    _, error = _require_admin()
    if error: return error

    plan = db_session.query(Insurance).filter(Insurance.insurance_id == plan_id).first()
    if not plan:
        return jsonify({'status': 'error', 'message': 'Insurance plan not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'Request body is required'}), 400

    try:
        if 'plan_name' in data: plan.plan_name = str(data['plan_name']).strip()
        if 'plan_type' in data: plan.plan_type = str(data['plan_type']).strip()
        if 'min_age' in data: plan.min_age = int(data['min_age'])
        if 'max_age' in data: plan.max_age = int(data['max_age'])
        if 'coverage_amount' in data: plan.coverage_amount = float(data['coverage_amount'])
        if 'has_critical_illness' in data: plan.has_critical_illness = 1 if data['has_critical_illness'] else 0
        if 'has_maternity' in data: plan.has_maternity = 1 if data['has_maternity'] else 0
        if 'has_accident' in data: plan.has_accident = 1 if data['has_accident'] else 0
        if 'co_pay_percentage' in data: plan.co_pay_percentage = int(data['co_pay_percentage'])
        if 'monthly_premium' in data: plan.monthly_premium = float(data['monthly_premium'])
        if 'irdai_uin' in data: plan.irdai_uin = _clean_uin(data['irdai_uin'])

        db_session.commit()
        db_session.refresh(plan)
        return jsonify({'status': 'success', 'message': 'Plan updated', 'data': plan.to_dict()}), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({'status': 'error', 'message': f'Failed to update plan: {str(e)}'}), 400


@admin_bp.route('/insurance/<int:plan_id>', methods=['DELETE'])
def delete_insurance(plan_id):
    _, error = _require_admin()
    if error: return error

    plan = db_session.query(Insurance).filter(Insurance.insurance_id == plan_id).first()
    if not plan:
        return jsonify({'status': 'error', 'message': 'Insurance plan not found'}), 404

    try:
        db_session.delete(plan)
        db_session.commit()
        return jsonify({'status': 'success', 'message': f'Plan {plan_id} deleted successfully', 'data': {}}), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({'status': 'error', 'message': f'Failed to delete plan: {str(e)}'}), 500


# =====================================================================
# SYSTEM SETTINGS
# =====================================================================

@admin_bp.route('/settings', methods=['GET'])
def list_settings():
    _, error = _require_admin()
    if error: return error
    settings = db_session.query(SystemSetting).order_by(SystemSetting.setting_key).all()
    return jsonify({'status': 'success', 'message': 'Fetched settings', 'data': [s.to_dict() for s in settings]}), 200


@admin_bp.route('/settings', methods=['PUT'])
def update_settings():
    _, error = _require_admin()
    if error: return error

    data = request.get_json()
    if not data or not isinstance(data.get('settings'), dict):
        return jsonify({'status': 'error', 'message': 'Request body must contain a "settings" dict'}), 400

    try:
        for key, value in data['settings'].items():
            setting = db_session.query(SystemSetting).filter(SystemSetting.setting_key == key).first()
            if setting:
                setting.setting_value = str(value)
            else:
                db_session.add(SystemSetting(setting_key=str(key), setting_value=str(value)))
        db_session.commit()
        updated = db_session.query(SystemSetting).order_by(SystemSetting.setting_key).all()
        return jsonify({'status': 'success', 'message': 'Settings updated', 'data': [s.to_dict() for s in updated]}), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({'status': 'error', 'message': f'Failed to update settings: {str(e)}'}), 500


# =====================================================================
# EXPENSE CATEGORIES
# =====================================================================

@admin_bp.route('/categories', methods=['GET'])
def list_categories():
    _, error = _require_admin()
    if error: return error
    cats = db_session.query(ExpenseCategory).order_by(ExpenseCategory.category_name).all()
    return jsonify({'status': 'success', 'message': 'Fetched categories', 'data': [c.to_dict() for c in cats]}), 200


@admin_bp.route('/categories', methods=['POST'])
def create_category():
    _, error = _require_admin()
    if error: return error

    data = request.get_json()
    if not data or not data.get('category_name'):
        return jsonify({'status': 'error', 'message': 'category_name is required'}), 400

    try:
        cat = ExpenseCategory(category_name=str(data['category_name']).strip(), icon=str(data.get('icon', 'category')).strip())
        db_session.add(cat)
        db_session.commit()
        db_session.refresh(cat)
        return jsonify({'status': 'success', 'message': 'Category created', 'data': cat.to_dict()}), 201
    except Exception as e:
        db_session.rollback()
        return jsonify({'status': 'error', 'message': f'Failed to create category: {str(e)}'}), 500


@admin_bp.route('/categories/<int:cat_id>', methods=['PUT'])
def update_category(cat_id):
    _, error = _require_admin()
    if error: return error

    cat = db_session.query(ExpenseCategory).filter(ExpenseCategory.category_id == cat_id).first()
    if not cat: return jsonify({'status': 'error', 'message': 'Category not found'}), 404

    data = request.get_json()
    if not data: return jsonify({'status': 'error', 'message': 'Request body is required'}), 400

    try:
        if 'category_name' in data: cat.category_name = str(data['category_name']).strip()
        if 'icon' in data: cat.icon = str(data['icon']).strip()
        db_session.commit()
        db_session.refresh(cat)
        return jsonify({'status': 'success', 'message': 'Category updated', 'data': cat.to_dict()}), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({'status': 'error', 'message': f'Failed to update category: {str(e)}'}), 500


@admin_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
def delete_category(cat_id):
    _, error = _require_admin()
    if error: return error

    cat = db_session.query(ExpenseCategory).filter(ExpenseCategory.category_id == cat_id).first()
    if not cat: return jsonify({'status': 'error', 'message': 'Category not found'}), 404

    try:
        db_session.delete(cat)
        db_session.commit()
        return jsonify({'status': 'success', 'message': f'Category {cat_id} deleted successfully', 'data': {}}), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({'status': 'error', 'message': f'Failed to delete category: {str(e)}'}), 500


# =====================================================================
# USERS (READ-ONLY)
# =====================================================================

@admin_bp.route('/users', methods=['GET'])
def list_users():
    _, error = _require_admin()
    if error: return error
    users = db_session.query(User).order_by(User.user_id).all()
    return jsonify({'status': 'success', 'message': 'Fetched users', 'data': [u.to_dict() for u in users]}), 200


# =====================================================================
# IRDAI PRODUCT CATALOGUE
# Source: https://irdai.gov.in/health-insurance-products
# The site doesn't allow bots (robots.txt), so we never fetch it ourselves.
# The admin saves/copies the table in a browser and uploads it here.
# =====================================================================

@admin_bp.route('/irdai/import', methods=['POST'])
def irdai_import():
    _, error = _require_admin()
    if error: return error

    text = None
    upload = request.files.get('file')
    if upload and upload.filename:
        raw = upload.read()
        for encoding in ('utf-8-sig', 'cp1252', 'latin-1'):
            try:
                text = raw.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
    else:
        data = request.get_json(silent=True) or {}
        text = data.get('text')

    if not text:
        return jsonify({'status': 'error', 'message': 'Upload a file or paste the IRDAI table'}), 400

    try:
        summary = import_products(text)
        msg = f"Imported {summary['added']} new and updated {summary['updated']} IRDAI products"
        return jsonify({'status': 'success', 'message': msg, 'data': summary}), 200
    except ValueError as e:
        db_session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except Exception as e:
        db_session.rollback()
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'Import failed: {str(e)}'}), 500


@admin_bp.route('/irdai/products', methods=['GET'])
def irdai_products():
    _, error = _require_admin()
    if error: return error

    q = (request.args.get('q') or '').strip()
    product_type = (request.args.get('type') or '').strip()
    limit = min(max(request.args.get('limit', 25, type=int), 1), 200)
    offset = max(request.args.get('offset', 0, type=int), 0)

    query = db_session.query(IrdaiProduct)
    if q:
        like = f'%{q}%'
        query = query.filter((IrdaiProduct.product_name.like(like)) |
                             (IrdaiProduct.insurer_name.like(like)) |
                             (IrdaiProduct.uin.like(like)))
    if product_type:
        query = query.filter(IrdaiProduct.product_type == product_type)

    total = query.count()
    items = query.order_by(IrdaiProduct.approval_date.desc(), IrdaiProduct.product_id.desc())                  .offset(offset).limit(limit).all()

    # Which of these products already have a ValueTrack plan?
    uins = [p.uin for p in items]
    linked = {}
    if uins:
        for plan in db_session.query(Insurance).filter(Insurance.irdai_uin.in_(uins)).all():
            linked.setdefault(plan.irdai_uin, []).append(plan.insurance_id)

    types = [t for (t,) in db_session.query(IrdaiProduct.product_type).distinct().all() if t]

    data = {
        'items': [dict(p.to_dict(), linked_plan_ids=linked.get(p.uin, [])) for p in items],
        'total': total,
        'limit': limit,
        'offset': offset,
        'types': sorted(types),
    }
    return jsonify({'status': 'success', 'message': 'Fetched IRDAI products', 'data': data}), 200
