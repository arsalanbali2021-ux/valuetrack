"""
ValueTrack -- Insurance Scoring Unit Tests
Test the scoring formula directly (no DB required).
Covers: pre-existing condition, tiny budget, age out of range.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import MagicMock


def _make_policy(insurance_id=1, provider='Test', plan='Plan',
                 min_age=18, max_age=65, premium=10000.0,
                 coverage=500000.0, pre_existing_allowed=0):
    """Create a mock policy object."""
    policy = MagicMock()
    policy.insurance_id = insurance_id
    policy.provider_name = provider
    policy.plan_name = plan
    policy.min_age = min_age
    policy.max_age = max_age
    policy.premium = premium
    policy.coverage_amount = coverage
    policy.pre_existing_allowed = pre_existing_allowed
    return policy


def test_score_pre_existing_condition():
    """
    User WITH pre-existing condition:
    - Policy that doesn't allow it -> PreExistingSupport = 0
    - Policy that allows it -> PreExistingSupport = 1
    """
    from services.insurance_service import _calculate_score

    # Policy does NOT allow pre-existing
    policy_no = _make_policy(pre_existing_allowed=0)
    score_no, _ = _calculate_score(policy_no, age=30, pre_existing=True,
                                 annual_budget=15000, max_coverage=500000)

    # Policy DOES allow pre-existing
    policy_yes = _make_policy(pre_existing_allowed=1)
    score_yes, _ = _calculate_score(policy_yes, age=30, pre_existing=True,
                                  annual_budget=15000, max_coverage=500000)

    # The one that allows should score higher (by 0.20 weight)
    assert score_yes > score_no, \
        f"Policy with pre-existing support ({score_yes}) should score higher than without ({score_no})"

    # When user has NO pre-existing, both should get full PreExistingSupport
    score_no_cond, _ = _calculate_score(policy_no, age=30, pre_existing=False,
                                      annual_budget=15000, max_coverage=500000)
    score_yes_cond, _ = _calculate_score(policy_yes, age=30, pre_existing=False,
                                       annual_budget=15000, max_coverage=500000)
    assert score_no_cond == score_yes_cond, \
        "Without pre-existing condition, both policies should score equally on that component"

    print("[PASS] test_score_pre_existing_condition")


def test_tiny_budget():
    """
    User with very small budget vs. expensive policies.
    BudgetFit should be low or zero.
    """
    from services.insurance_service import _calculate_score

    # Premium 20000 but budget only 5000
    policy = _make_policy(premium=20000, coverage=500000)
    score, _ = _calculate_score(policy, age=30, pre_existing=False,
                              annual_budget=5000, max_coverage=500000)

    # BudgetFit = max(0, 1 - (20000-5000)/5000) = max(0, 1-3) = 0
    # Score = AgeMatch*0.30 + 0*0.40 + 1*0.20 + (500000/500000)*0.10
    #       = 0.30 + 0 + 0.20 + 0.10 = 0.60
    expected = 0.60
    assert abs(score - expected) < 0.001, \
        f"Score {score} should be close to {expected} for tiny budget"

    # Zero budget
    score_zero, _ = _calculate_score(policy, age=30, pre_existing=False,
                                   annual_budget=0, max_coverage=500000)
    # BudgetFit = 0 (special case for zero budget)
    expected_zero = 0.30 + 0.0 + 0.20 + 0.10  # = 0.60
    assert abs(score_zero - expected_zero) < 0.001, \
        f"Zero budget score {score_zero} should be {expected_zero}"

    print("[PASS] test_tiny_budget")


def test_age_out_of_range():
    """
    User age outside policy's min_age -- max_age range.
    AgeMatch should be 0, reducing score significantly.
    """
    from services.insurance_service import _calculate_score

    # Policy for 18-35 but user is 50
    policy = _make_policy(min_age=18, max_age=35, premium=5000, coverage=300000)
    score, _ = _calculate_score(policy, age=50, pre_existing=False,
                              annual_budget=15000, max_coverage=500000)

    # AgeMatch = 0
    # BudgetFit = 1 (5000 <= 15000)
    # PreExisting = 1
    # CoverageBonus = 300000/500000 = 0.6
    # Score = 0 + 0.40 + 0.20 + 0.06 = 0.66
    assert score < 0.70, f"Out-of-range age should reduce score, got {score}"

    # Within range
    score_in, _ = _calculate_score(policy, age=25, pre_existing=False,
                                 annual_budget=15000, max_coverage=500000)
    assert score_in > score, \
        f"In-range ({score_in}) should score higher than out-of-range ({score})"

    print("[PASS] test_age_out_of_range")


def test_score_ordering():
    """Policies should be ordered by score descending."""
    from services.insurance_service import _calculate_score

    policies = [
        _make_policy(insurance_id=1, premium=5000, coverage=300000,
                     min_age=18, max_age=65, pre_existing_allowed=0),
        _make_policy(insurance_id=2, premium=8000, coverage=500000,
                     min_age=18, max_age=65, pre_existing_allowed=1),
        _make_policy(insurance_id=3, premium=25000, coverage=2000000,
                     min_age=25, max_age=45, pre_existing_allowed=1),
    ]
    max_cov = 2000000.0

    scored = []
    for p in policies:
        s, _ = _calculate_score(p, age=30, pre_existing=True,
                              annual_budget=10000, max_coverage=max_cov)
        scored.append((p.insurance_id, s))

    scored.sort(key=lambda x: x[1], reverse=True)

    # Verify descending order
    for i in range(len(scored) - 1):
        assert scored[i][1] >= scored[i + 1][1], \
            f"Score ordering violated: {scored[i]} should >= {scored[i+1]}"

    print("[PASS] test_score_ordering")


if __name__ == '__main__':
    test_score_pre_existing_condition()
    test_tiny_budget()
    test_age_out_of_range()
    test_score_ordering()
    print("\nAll insurance scoring tests passed!")
