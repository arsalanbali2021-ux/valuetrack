"""
ValueTrack — Insurance Scoring Service
Rule-based insurance plan scorer. No ML.

Scoring Components (weights):
  AgeMatch          (0.30) — 1 if min_age <= age <= max_age, else 0
  BudgetFit         (0.40) — 1 if premium <= budget, else max(0, 1 - (premium-budget)/budget)
  PreExistingSupport(0.20) — 1 if no condition OR policy allows it, else 0
  CoverageBonus     (0.10) — coverage / max_coverage across all policies

Composite: score = AgeMatch*0.30 + BudgetFit*0.40 + PreExistingSupport*0.20 + CoverageBonus*0.10
Top 5 results stored in insurance_result with rank_position 1..5.
"""
from decimal import Decimal
from models import Insurance, InsuranceRequest, InsuranceResult
from db import db_session
from sqlalchemy import func as sql_func


def _calculate_score(policy, age: int, pre_existing: bool,
                     annual_budget: float, max_coverage: float) -> float:
    """Calculate composite score for a single policy."""

    # AgeMatch
    age_match = 1.0 if policy.min_age <= age <= policy.max_age else 0.0

    # BudgetFit
    premium = float(policy.premium)
    if annual_budget <= 0:
        budget_fit = 0.0
    elif premium <= annual_budget:
        budget_fit = 1.0
    else:
        budget_fit = max(0.0, 1.0 - (premium - annual_budget) / annual_budget)

    # PreExistingSupport
    if not pre_existing:
        pre_existing_support = 1.0
    else:
        pre_existing_support = 1.0 if policy.pre_existing_allowed else 0.0

    # CoverageBonus
    coverage = float(policy.coverage_amount)
    coverage_bonus = coverage / max_coverage if max_coverage > 0 else 0.0

    # Composite score
    score = (
        age_match * 0.30 +
        budget_fit * 0.40 +
        pre_existing_support * 0.20 +
        coverage_bonus * 0.10
    )

    return round(score, 4)


def score_insurance(user_id: int, age: int, pre_existing_condition: bool,
                    annual_budget: float) -> dict:
    """
    Score all insurance policies for the given user profile.
    Persists top 5 results in insurance_result.

    Returns:
        {
            "request_id": int,
            "top": [{"insurance_id": int, "score": float, "rank": int,
                      "provider": str, "plan_name": str, "premium": float,
                      "coverage": float}, ...]
        }
    """
    # Validate
    if age <= 0 or age > 120:
        raise ValueError("Age must be between 1 and 120")
    if annual_budget < 0:
        raise ValueError("Annual budget cannot be negative")

    # Create request record
    request = InsuranceRequest(
        user_id=user_id,
        age=age,
        pre_existing_condition=1 if pre_existing_condition else 0,
        annual_budget=annual_budget
    )
    db_session.add(request)
    db_session.flush()

    # Fetch all policies
    policies = db_session.query(Insurance).all()
    if not policies:
        db_session.commit()
        return {
            'request_id': request.request_id,
            'top': [],
            'reason': 'no policies in database'
        }

    # Get max coverage for normalization
    max_coverage = float(
        db_session.query(sql_func.max(Insurance.coverage_amount)).scalar() or 0
    )

    # Score each policy
    scored = []
    for policy in policies:
        score = _calculate_score(policy, age, pre_existing_condition,
                                 annual_budget, max_coverage)
        scored.append((policy, score))

    # Sort descending by score
    scored.sort(key=lambda x: x[1], reverse=True)

    # Filter out zero-score policies
    scored = [(p, s) for p, s in scored if s > 0]

    if not scored:
        db_session.commit()
        return {
            'request_id': request.request_id,
            'top': [],
            'reason': 'no eligible plans'
        }

    # Take top 5
    top5 = scored[:5]

    # Persist results
    results = []
    for rank, (policy, score) in enumerate(top5, start=1):
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
            'provider': policy.provider_name,
            'plan_name': policy.plan_name,
            'premium': float(policy.premium),
            'coverage': float(policy.coverage_amount)
        })

    db_session.commit()

    return {
        'request_id': request.request_id,
        'top': results
    }


def get_results(request_id: int) -> dict:
    """Fetch persisted insurance ranking for a given request."""
    request = db_session.query(InsuranceRequest).filter(
        InsuranceRequest.request_id == request_id
    ).first()

    if not request:
        raise ValueError("Request not found")

    results = db_session.query(InsuranceResult).filter(
        InsuranceResult.request_id == request_id
    ).order_by(InsuranceResult.rank_position).all()

    top = []
    for r in results:
        policy = db_session.query(Insurance).filter(
            Insurance.insurance_id == r.insurance_id
        ).first()
        top.append({
            'insurance_id': r.insurance_id,
            'score': float(r.rank_score),
            'rank': r.rank_position,
            'provider': policy.provider_name if policy else 'Unknown',
            'plan_name': policy.plan_name if policy else 'Unknown',
            'premium': float(policy.premium) if policy else 0,
            'coverage': float(policy.coverage_amount) if policy else 0
        })

    return {
        'request_id': request_id,
        'top': top
    }
