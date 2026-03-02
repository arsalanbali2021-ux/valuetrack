"""
ValueTrack — Insurance Recommendations Service
Scoring logic to match user profile against available insurance plans using new schema.
"""
from models import Insurance, InsuranceRequest, InsuranceResult
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

    explanations.append({'icon': 'check_circle', 'text': f'Age {policy.min_age}-{policy.max_age} limit met'})
    explanations.append({'icon': 'payments', 'text': f'Under budget: ₹{premium}/mo'})

    score = 0.5

    # Scoring Criteria: Critical Illness
    if needs_critical_illness:
        if policy.has_critical_illness:
            score += 0.15
            explanations.append({'icon': 'health_and_safety', 'text': 'Critical Illness Covered'})
        else:
            explanations.append({'icon': 'error', 'text': 'NO Critical Illness Cover'})
    elif policy.has_critical_illness:
        explanations.append({'icon': 'info', 'text': 'Bonus: Critical Illness Covered'})

    # Scoring Criteria: Maternity
    if needs_maternity:
        if policy.has_maternity:
            score += 0.15
            explanations.append({'icon': 'pregnant_woman', 'text': 'Maternity Covered'})
        else:
            explanations.append({'icon': 'error', 'text': 'NO Maternity Cover'})
            
    # Scoring Criteria: Accident
    if needs_accident:
        if policy.has_accident:
            score += 0.10
            explanations.append({'icon': 'personal_injury', 'text': 'Accident Covered'})
        else:
             explanations.append({'icon': 'error', 'text': 'NO Accident Cover'})

    # Coverage Bonus
    coverage = float(policy.coverage_amount)
    coverage_bonus = (coverage / max_coverage) if max_coverage > 0 else 0.0
    score += (coverage_bonus * 0.10)

    return round(score, 4), explanations


def score_insurance(user_id: int, age: int, needs_critical_illness: bool,
                    needs_maternity: bool, needs_accident: bool,
                    monthly_budget: float) -> dict:
    """Score all insurance policies and persist top 5 results."""
    if age <= 0 or age > 120:
        raise ValueError("Age must be between 1 and 120")
    if monthly_budget < 0:
        raise ValueError("Budget cannot be negative")

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

    policies = db_session.query(Insurance).all()
    if not policies:
        db_session.commit()
        return {'request_id': request.request_id, 'top': [], 'reason': 'no policies in database'}

    max_coverage = float(db_session.query(sql_func.max(Insurance.coverage_amount)).scalar() or 0)

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
        return {'request_id': request.request_id, 'top': [], 'reason': 'no eligible plans fit your criteria'}

    top5 = scored[:5]
    results = []
    for rank, (policy, score, explanations) in enumerate(top5, start=1):
        result = InsuranceResult(
            request_id=request.request_id,
            insurance_id=policy.insurance_id,
            rank_score=score,
            rank_position=rank
        )
        db_session.add(result)
        results.append({
            'insurance_id': policy.insurance_id,
            'score': score,
            'rank': rank,
            'type': policy.plan_type,
            'plan_name': policy.plan_name,
            'premium': float(policy.monthly_premium),
            'coverage': float(policy.coverage_amount),
            'co_pay': policy.co_pay_percentage,
            'has_maternity': bool(policy.has_maternity),
            'has_critical_illness': bool(policy.has_critical_illness),
            'has_accident': bool(policy.has_accident),
            'min_age': policy.min_age,
            'max_age': policy.max_age,
            'explanations': explanations
        })

    db_session.commit()
    return {'request_id': request.request_id, 'top': results}

def get_results(request_id: int) -> dict:
    """Fetch persisted insurance ranking."""
    request = db_session.query(InsuranceRequest).filter(InsuranceRequest.request_id == request_id).first()
    if not request: raise ValueError("Request not found")

    results = db_session.query(InsuranceResult).filter(InsuranceResult.request_id == request_id).order_by(InsuranceResult.rank_position).all()
    max_coverage = float(db_session.query(sql_func.max(Insurance.coverage_amount)).scalar() or 0)

    top = []
    for r in results:
        policy = db_session.query(Insurance).filter(Insurance.insurance_id == r.insurance_id).first()
        explanations = []
        if policy:
            _, explanations = _calculate_score(policy, request.age, bool(request.needs_critical_illness),
                                               bool(request.needs_maternity), bool(request.needs_accident),
                                               float(request.monthly_budget), max_coverage)

        top.append({
            'insurance_id': r.insurance_id,
            'score': float(r.rank_score),
            'rank': r.rank_position,
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
            'explanations': explanations
        })

    return {'request_id': request_id, 'top': top}
