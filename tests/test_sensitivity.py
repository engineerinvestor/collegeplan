"""Tests for sensitivity analysis sweep mechanics."""

import pytest

from collegeplan import (
    Assumptions,
    Child,
    CostProfile,
    run_sensitivity,
)


@pytest.fixture
def sweep_child():
    profile = CostProfile(label="Sweep", current_total_cost=30_000, annual_cost_growth=0.04)
    return Child(name="SW", current_age=12, cost_profile=profile, start_age=18, attendance_years=4)


@pytest.fixture
def sweep_assumptions():
    return Assumptions(expected_return_nominal=0.07, general_inflation=0.03)


def test_grid_produces_correct_count(sweep_child, sweep_assumptions):
    """2 return values x 2 inflation values = 4 scenarios."""
    grid = {
        "expected_return_nominal": [0.05, 0.08],
        "general_inflation": [0.02, 0.04],
    }
    result = run_sensitivity([sweep_child], sweep_assumptions, grid)
    assert len(result.scenarios) == 4


def test_scenarios_have_solutions(sweep_child, sweep_assumptions):
    grid = {"expected_return_nominal": [0.05, 0.07]}
    result = run_sensitivity([sweep_child], sweep_assumptions, grid)
    for case in result.scenarios:
        assert case.savings_solution is not None
        assert case.savings_solution.required_annual_contribution >= 0


def test_higher_return_needs_less_savings(sweep_child, sweep_assumptions):
    """Higher expected return should require lower annual savings."""
    grid = {"expected_return_nominal": [0.04, 0.10]}
    result = run_sensitivity([sweep_child], sweep_assumptions, grid)
    low_return = result.scenarios[0].savings_solution
    high_return = result.scenarios[1].savings_solution
    assert high_return.required_annual_contribution < low_return.required_annual_contribution


def test_sensitivity_escalation_sweep(sweep_child, sweep_assumptions):
    """Higher growth rates produce lower required savings."""
    grid = {"contribution_growth_rate": [0.0, 0.05]}
    result = run_sensitivity([sweep_child], sweep_assumptions, grid)
    no_growth = result.scenarios[0].savings_solution
    with_growth = result.scenarios[1].savings_solution
    assert with_growth.required_annual_contribution < no_growth.required_annual_contribution
