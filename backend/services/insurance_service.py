"""
ValueTrack — Insurance Recommendations Service
Scoring logic to match user profile against available insurance plans using new schema.
"""
from models import Insurance, InsuranceRequest, InsuranceResult, IrdaiProduct
from db import db_session
from sqlalchemy import func as sql_func

def _calculate_score(policy: Insurance, age: int, 
                     needs_critical_illness: bool,
                     needs_maternity: bool,
                     needs_accident: bool,
                     monthly_budget: float, 
                     max_coverage: float = 1.0) -> tuple:
    """Calculate composite score and generate explanations for a single policy."""
    explanations = []

    # Hard Filter 1: Age
    if not (policy.min_age <= age <= policy.max_age):
        return 0.0, []

    # Hard Filter 2: Budget
    premium = float(policy.monthly_premium)
    if premium > monthly_budget:
         return 0.0, []

    explanations.append({'icon': 'check_circle', 'text': f'Age limit {policy.min_age}–{policy.max_age} fits'})
    explanations.append({'icon': 'payments', 'text': f'Within budget at ₹{premium:,.0f} a month'})

    score = 0.5

    # Scoring Criteria: Critical Illness
    if needs_critical_illness:
        if policy.has_critical_illness:
            score += 0.15
            explanations.append({'icon': 'health_and_safety', 'text': 'Covers critical illness'})
        else:
            explanations.append({'icon': 'error', 'text': 'No critical illness cover'})
    elif policy.has_critical_illness:
        explanations.append({'icon': 'info', 'text': 'Also covers critical illness'})

    # Scoring Criteria: Maternity
    if needs_maternity:
        if policy.has_maternity:
            score += 0.15
            explanations.append({'icon': 'pregnant_woman', 'text': 'Covers maternity'})
        else:
            explanations.append({'icon': 'error', 'text': 'No maternity cover'})
            
    # Scoring Criteria: Accident
    if needs_accident:
        if policy.has_accident:
            score += 0.10
            explanations.append({'icon': 'personal_injury', 'text': 'Covers accidents'})
        else:
             explanations.append({'icon': 'error', 'text': 'No accident cover'})

    # Coverage Bonus
    coverage = float(policy.coverage_amount)
    coverage_bonus = (coverage / max_coverage) if max_coverage > 0 else 0.0
    score += (coverage_bonus * 0.10)

    return round(score, 4), explanations


SOURCES = ('all', 'irdai')


def _irdai_lookup(policies) -> dict:
    """Map UIN -> IrdaiProduct for the policies that are linked to one."""
    uins = {p.irdai_uin for p in policies if getattr(p, 'irdai_uin', None)}
    if not uins:
        return {}
    rows = db_session.query(IrdaiProduct).filter(IrdaiProduct.uin.in_(uins)).all()
    return {r.uin: r for r in rows}


def _irdai_explanation(policy, irdai_map):
    product = irdai_map.get(policy.irdai_uin) if getattr(policy, 'irdai_uin', None) else None
    if not product:
        return None
    if product.is_archived:
        return {'icon': 'warning', 'text': f'Archived by IRDAI (UIN {product.uin})'}
    return {'icon': 'verified', 'text': f'Registered with IRDAI, UIN {product.uin}'}


def _result_dict(policy, score, rank, explanations, irdai_map):
    product = irdai_map.get(policy.irdai_uin) if policy and getattr(policy, 'irdai_uin', None) else None
    return {
        'insurance_id': policy.insurance_id if policy else None,
        'score': score,
        'rank': rank,
        'type': policy.plan_type if policy else 'Unknown',
        'plan_name': policy.plan_name if policy else 'Unknown',
        'premium': float(policy.monthly_premium) if policy else 0,
        'coverage': float(policy.coverage_amount) if policy else 0,
        'co_pay': policy.co_pay_percentage if policy else 0,
        'has_maternity': bool(policy.has_maternity) if policy else False,
        'has_critical_illness': bool(policy.has_critical_illness) if policy else False,
        'has_accident': bool(policy.has_accident) if policy else False,
        'min_age': policy.min_age if policy else 0,
        'max_age': policy.max_age if policy else 0,
        'explanations': explanations,
        'irdai': {
            'uin': product.uin,
            'insurer': product.insurer_name,
            'product_name': product.product_name,
            'product_type': product.product_type,
            'approval_date': str(product.approval_date) if product.approval_date else None,
            'is_archived': bool(product.is_archived),
        } if product else None,
    }


def score_insurance(user_id: int, age: int, needs_critical_illness: bool,
                    needs_maternity: bool, needs_accident: bool,
                    monthly_budget: float, source: str = 'all') -> dict:
    """
    Score insurance policies and persist the top 5 results.
    source='all'   -> every plan in the insurance table
    source='irdai' -> only plans linked to a current (non-archived) IRDAI product
    """
    if age <= 0 or age > 120:
        raise ValueError("Age must be between 1 and 120")
    if monthly_budget < 0:
        raise ValueError("Budget cannot be negative")
    source = (source or 'all').lower()
    if source not in SOURCES:
        raise ValueError("source must be 'all' or 'irdai'")

    request = InsuranceRequest(
        user_id=user_id,
        age=age,
        needs_critical_illness=1 if needs_critical_illness else 0,
        needs_maternity=1 if needs_maternity else 0,
        needs_accident=1 if needs_accident else 0,
        monthly_budget=monthly_budget
    )
    db_session.add(request)
    db_session.flush()

    query = db_session.query(Insurance)
    if source == 'irdai':
        query = query.join(IrdaiProduct, IrdaiProduct.uin == Insurance.irdai_uin) \
                     .filter(IrdaiProduct.is_archived == 0)
    policies = query.all()

    if not policies:
        db_session.commit()
        if source == 'irdai':
            reason = ('No IRDAI-registered plans yet. An admin can import the IRDAI product list '
                      'and link plans to it from the admin panel.')
        else:
            reason = 'no policies in database'
        return {'request_id': request.request_id, 'source': source, 'top': [], 'reason': reason}

    max_coverage = float(db_session.query(sql_func.max(Insurance.coverage_amount)).scalar() or 0)
    irdai_map = _irdai_lookup(policies)

    scored = []
    for policy in policies:
        score, explanations = _calculate_score(policy, age, needs_critical_illness,
                                               needs_maternity, needs_accident,
                                               monthly_budget, max_coverage)
        scored.append((policy, score, explanations))

    scored.sort(key=lambda x: x[1], reverse=True)
    scored = [(p, s, e) for p, s, e in scored if s > 0]

    if not scored:
        db_session.commit()
        return {'request_id': request.request_id, 'source': source, 'top': [],
                'reason': 'no eligible plans fit your criteria'}

    results = []
    for rank, (policy, score, explanations) in enumerate(scored[:5], start=1):
        db_session.add(InsuranceResult(
            request_id=request.request_id,
            insurance_id=policy.insurance_id,
            rank_score=score,
            rank_position=rank
        ))
        badge = _irdai_explanation(policy, irdai_map)
        if badge:
            explanations = [badge] + explanations
        results.append(_result_dict(policy, score, rank, explanations, irdai_map))

    db_session.commit()
    return {'request_id': request.request_id, 'source': source, 'top': results}


def get_results(request_id: int) -> dict:
    """Fetch persisted insurance ranking."""
    request = db_session.query(InsuranceRequest).filter(InsuranceRequest.request_id == request_id).first()
    if not request:
        raise ValueError("Request not found")

    results = db_session.query(InsuranceResult).filter(
        InsuranceResult.request_id == request_id).order_by(InsuranceResult.rank_position).all()
    max_coverage = float(db_session.query(sql_func.max(Insurance.coverage_amount)).scalar() or 0)

    policies = {}
    for r in results:
        policies[r.insurance_id] = db_session.query(Insurance).filter(
            Insurance.insurance_id == r.insurance_id).first()
    irdai_map = _irdai_lookup([p for p in policies.values() if p])

    top = []
    for r in results:
        policy = policies.get(r.insurance_id)
        explanations = []
        if policy:
            _, explanations = _calculate_score(policy, request.age, bool(request.needs_critical_illness),
                                               bool(request.needs_maternity), bool(request.needs_accident),
                                               float(request.monthly_budget), max_coverage)
            badge = _irdai_explanation(policy, irdai_map)
            if badge:
                explanations = [badge] + explanations
        item = _result_dict(policy, float(r.rank_score), r.rank_position, explanations, irdai_map)
        item['insurance_id'] = r.insurance_id
        top.append(item)

    return {'request_id': request_id, 'top': top}
