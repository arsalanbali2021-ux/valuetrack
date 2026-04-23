"""
ValueTrack -- Insurance Scoring Unit Tests
Tests the scoring formula directly (no DB required).

Scoring recap (services/insurance_service.py):
  hard filters: age within min_age..max_age, monthly_premium <= budget
  base 0.50
  +0.15 critical illness (if needed and covered)
  +0.15 maternity        (if needed and covered)
  +0.10 accident         (if needed and covered)
  +0.10 * coverage / max_coverage
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from types import SimpleNamespace

from services.insurance_service import _calculate_score


def _make_policy(insurance_id=1, min_age=18, max_age=65, premium=800.0,
                 coverage=500000.0, critical=0, maternity=0, accident=0):
    """Plain object with the same fields as the Insurance model."""
    return SimpleNamespace(
        insurance_id=insurance_id,
        plan_name=f'Plan {insurance_id}',
        plan_type='Individual',
        min_age=min_age,
        max_age=max_age,
        monthly_premium=premium,
        coverage_amount=coverage,
        has_critical_illness=critical,
        has_maternity=maternity,
        has_accident=accident,
        co_pay_percentage=0,
    )


def _score(policy, age=30, ci=False, mat=False, acc=False, budget=1000.0, max_cov=500000.0):
    return _calculate_score(policy, age, ci, mat, acc, budget, max_cov)


def test_age_out_of_range_is_filtered():
    policy = _make_policy(min_age=18, max_age=35)

    score, reasons = _score(policy, age=50)
    assert score == 0.0
    assert reasons == []

    # Edges of the range are allowed
    assert _score(policy, age=18)[0] > 0
    assert _score(policy, age=35)[0] > 0


def test_over_budget_is_filtered():
    policy = _make_policy(premium=1500)

    score, reasons = _score(policy, budget=1000)
    assert score == 0.0
    assert reasons == []

    # Premium exactly equal to budget is fine
    assert _score(policy, budget=1500)[0] > 0


def test_base_score_with_no_needs():
    # No needs ticked, plan has the biggest coverage -> 0.50 + 0.10
    policy = _make_policy(coverage=500000)
    score, reasons = _score(policy, max_cov=500000)
    assert abs(score - 0.60) < 1e-9
    assert any('limit met' in r['text'] for r in reasons)
    assert any('Under budget' in r['text'] for r in reasons)


def test_all_needs_covered_hits_max_score():
    policy = _make_policy(coverage=500000, critical=1, maternity=1, accident=1)
    score, _ = _score(policy, ci=True, mat=True, acc=True, max_cov=500000)
    assert abs(score - 1.0) < 1e-9


def test_each_need_adds_its_weight():
    base, _ = _score(_make_policy(coverage=0, critical=1, maternity=1, accident=1))
    ci, _ = _score(_make_policy(coverage=0, critical=1), ci=True)
    mat, _ = _score(_make_policy(coverage=0, maternity=1), mat=True)
    acc, _ = _score(_make_policy(coverage=0, accident=1), acc=True)

    assert abs(base - 0.50) < 1e-9
    assert abs(ci - 0.65) < 1e-9
    assert abs(mat - 0.65) < 1e-9
    assert abs(acc - 0.60) < 1e-9


def test_missing_cover_gives_no_points_and_says_so():
    policy = _make_policy(coverage=0, maternity=0)
    score, reasons = _score(policy, mat=True)
    assert abs(score - 0.50) < 1e-9
    assert any(r['text'] == 'NO Maternity Cover' for r in reasons)


def test_coverage_bonus_scales_with_coverage():
    half, _ = _score(_make_policy(coverage=250000), max_cov=500000)
    full, _ = _score(_make_policy(coverage=500000), max_cov=500000)
    assert abs(half - 0.55) < 1e-9
    assert abs(full - 0.60) < 1e-9


def test_zero_max_coverage_does_not_crash():
    score, _ = _score(_make_policy(coverage=0), max_cov=0)
    assert abs(score - 0.50) < 1e-9


def test_score_ordering():
    """A plan matching more needs should rank above one that matches fewer."""
    policies = [
        _make_policy(insurance_id=1, coverage=300000),
        _make_policy(insurance_id=2, coverage=500000, maternity=1),
        _make_policy(insurance_id=3, coverage=500000, maternity=1, critical=1),
        _make_policy(insurance_id=4, coverage=1000000, premium=5000, maternity=1, critical=1),
    ]
    scored = [(p.insurance_id, _score(p, ci=True, mat=True, budget=1000, max_cov=1000000)[0])
              for p in policies]
    scored = [s for s in scored if s[1] > 0]
    scored.sort(key=lambda x: x[1], reverse=True)

    # Plan 4 is over budget, so it's filtered out
    assert [pid for pid, _ in scored] == [3, 2, 1]
