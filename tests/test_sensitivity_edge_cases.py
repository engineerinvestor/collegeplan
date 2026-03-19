"""Edge-case tests for sensitivity analysis."""

import pytest

from collegeplan import (
    Assumptions,
    Child,
    CostProfile,
    run_sensitivity,
)


@pytest.fixture
def sens_child():
    profile = CostProfile(label="Sens", current_total_cost=30_000, annual_cost_growth=0.04)
    return Child(
        name="SensKid",
        current_age=10,
        cost_profile=profile,
        start_age=18,
        attendance_years=4,
    )


@pytest.fixture
def sens_assumptions():
    return Assumptions(expected_return_nominal=0.07, general_inflation=0.03)


def test_single_param_grid(sens_child, sens_assumptions):
    """A grid with one parameter and one value produces exactly one scenario."""
    grid = {"expected_return_nominal": [0.07]}
    result = run_sensitivity([sens_child], sens_assumptions, grid)
    assert len(result.scenarios) == 1
    assert result.scenarios[0].savings_solution is not None


def test_include_projection_populates_household_result(sens_child, sens_assumptions):
    """include_projection=True should attach household results to each case."""
    grid = {"expected_return_nominal": [0.06, 0.08]}
    result = run_sensitivity([sens_child], sens_assumptions, grid, include_projection=True)
    for case in result.scenarios:
        assert case.household_result is not None
        assert case.household_result.total_projected_spend > 0


def test_include_projection_false_omits_household_result(sens_child, sens_assumptions):
    """include_projection=False (default) leaves household_result as None."""
    grid = {"expected_return_nominal": [0.06, 0.08]}
    result = run_sensitivity([sens_child], sens_assumptions, grid)
    for case in result.scenarios:
        assert case.household_result is None


def test_annual_cost_growth_sweep(sens_child, sens_assumptions):
    """Higher cost growth should require more savings."""
    grid = {"annual_cost_growth": [0.02, 0.08]}
    result = run_sensitivity([sens_child], sens_assumptions, grid)
    low_growth = result.scenarios[0].savings_solution
    high_growth = result.scenarios[1].savings_solution
    assert low_growth is not None
    assert high_growth is not None
    assert high_growth.required_annual_contribution > low_growth.required_annual_contribution


def test_scholarship_pct_sweep(sens_child, sens_assumptions):
    """Higher scholarship percentage should require less savings."""
    grid = {"scholarship_pct": [0.0, 0.50]}
    result = run_sensitivity([sens_child], sens_assumptions, grid)
    no_scholarship = result.scenarios[0].savings_solution
    half_scholarship = result.scenarios[1].savings_solution
    assert no_scholarship is not None
    assert half_scholarship is not None
    assert (
        half_scholarship.required_annual_contribution < no_scholarship.required_annual_contribution
    )


def test_target_funding_ratio_in_grid(sens_child, sens_assumptions):
    """target_funding_ratio can be varied via the grid."""
    grid = {"target_funding_ratio": [0.50, 1.0]}
    result = run_sensitivity([sens_child], sens_assumptions, grid)
    half_target = result.scenarios[0].savings_solution
    full_target = result.scenarios[1].savings_solution
    assert half_target is not None
    assert full_target is not None
    assert half_target.required_annual_contribution < full_target.required_annual_contribution


def test_real_return_sweep(sens_child):
    """Grid can sweep expected_return_real instead of nominal."""
    assumptions = Assumptions(expected_return_real=0.04, general_inflation=0.03)
    grid = {"expected_return_real": [0.02, 0.06]}
    result = run_sensitivity([sens_child], assumptions, grid)
    assert len(result.scenarios) == 2
    low_return = result.scenarios[0].savings_solution
    high_return = result.scenarios[1].savings_solution
    assert low_return is not None
    assert high_return is not None
    assert high_return.required_annual_contribution < low_return.required_annual_contribution


def test_multi_dimensional_grid(sens_child, sens_assumptions):
    """3x2 grid produces 6 scenarios."""
    grid = {
        "expected_return_nominal": [0.05, 0.07, 0.09],
        "general_inflation": [0.02, 0.04],
    }
    result = run_sensitivity([sens_child], sens_assumptions, grid)
    assert len(result.scenarios) == 6


def test_each_scenario_has_parameters(sens_child, sens_assumptions):
    """Each scenario records its parameter values."""
    grid = {"expected_return_nominal": [0.05, 0.09]}
    result = run_sensitivity([sens_child], sens_assumptions, grid)
    params = [case.parameters["expected_return_nominal"] for case in result.scenarios]
    assert 0.05 in params
    assert 0.09 in params
