"""Tests for the required-savings solver."""

from dataclasses import replace

import pytest

from collegeplan import (
    Assumptions,
    Child,
    CostProfile,
    HouseholdFund,
    project_household_plan,
    solve_required_savings,
)


@pytest.fixture
def solver_child():
    profile = CostProfile(label="Test", current_total_cost=25_000, annual_cost_growth=0.04)
    return Child(name="S", current_age=10, cost_profile=profile, start_age=18, attendance_years=4)


@pytest.fixture
def solver_assumptions():
    return Assumptions(expected_return_nominal=0.06, general_inflation=0.03)


def test_already_funded_returns_zero(zero_return_assumptions):
    profile = CostProfile(label="T", current_total_cost=10_000, annual_cost_growth=0.0)
    child = Child(
        name="A", current_age=14, cost_profile=profile,
        start_age=18, attendance_years=4, current_529_balance=40_000,
    )
    sol = solve_required_savings([child], zero_return_assumptions)
    assert sol.required_annual_contribution == 0.0
    assert sol.achieved_funding_ratio >= 1.0


def test_solve_then_verify(solver_child, solver_assumptions):
    """Critical close-the-loop test: feed solved contribution back and verify funding."""
    sol = solve_required_savings([solver_child], solver_assumptions)
    assert sol.required_annual_contribution > 0

    # Feed solved contribution back
    per_child_contrib = sol.per_child_suggestions[solver_child.name]
    funded_child = replace(solver_child, annual_contribution=per_child_contrib)
    result = project_household_plan([funded_child], solver_assumptions)
    ratio = result.child_results[0].funded_ratio
    assert ratio >= 0.999, f"Funding ratio {ratio} is below 0.999"


def test_partial_funding_target(solver_child, solver_assumptions):
    """Solving for 75% funding should achieve ~0.75."""
    sol = solve_required_savings([solver_child], solver_assumptions, target_funding_ratio=0.75)
    assert abs(sol.achieved_funding_ratio - 0.75) < 0.01


def test_shared_pool_mode(solver_child, solver_assumptions):
    """Solver works in shared_pool mode."""
    sol = solve_required_savings([solver_child], solver_assumptions, solve_mode="shared_pool")
    assert sol.required_annual_contribution > 0

    # Verify
    hf = HouseholdFund(shared_annual_contribution=sol.required_annual_contribution)
    result = project_household_plan([solver_child], solver_assumptions, hf)
    total_funded = sum(cr.funded_amount for cr in result.child_results)
    total_cost = result.total_projected_spend
    assert total_funded / total_cost >= 0.999


def test_monthly_is_annual_over_12(solver_child, solver_assumptions):
    sol = solve_required_savings([solver_child], solver_assumptions)
    assert sol.required_monthly_contribution == pytest.approx(sol.required_annual_contribution / 12)
