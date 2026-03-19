"""Tests for reporting/serialization."""

import json

from collegeplan import (
    Assumptions,
    Child,
    CostProfile,
    project_child_plan,
    to_dict,
    to_json,
)
from collegeplan.models import SavingsSolution


def test_to_dict_rounds_dollars():
    profile = CostProfile(label="T", current_total_cost=10_000, annual_cost_growth=0.05)
    child = Child(name="A", current_age=14, cost_profile=profile, start_age=18, attendance_years=4)
    assumptions = Assumptions(expected_return_nominal=0.07, general_inflation=0.03)
    result = project_child_plan(child, assumptions)
    d = to_dict(result)
    assert isinstance(d["projected_total_cost"], int)
    assert isinstance(d["shortfall"], int)


def test_to_dict_preserves_ratios():
    profile = CostProfile(label="T", current_total_cost=10_000, annual_cost_growth=0.05)
    child = Child(
        name="A", current_age=14, cost_profile=profile,
        start_age=18, attendance_years=4, current_529_balance=20_000,
    )
    assumptions = Assumptions(expected_return_nominal=0.07, general_inflation=0.03)
    result = project_child_plan(child, assumptions)
    d = to_dict(result)
    assert isinstance(d["funded_ratio"], float)


def test_to_dict_converts_enums():
    sol = SavingsSolution(
        required_annual_contribution=1000,
        required_monthly_contribution=83.33,
        per_child_suggestions={"A": 1000},
        achieved_funding_ratio=0.95,
    )
    d = to_dict(sol)
    # Enum fields shouldn't appear in SavingsSolution, but ensure the function handles them
    assert isinstance(d["achieved_funding_ratio"], float)


def test_to_json_valid():
    profile = CostProfile(label="T", current_total_cost=10_000, annual_cost_growth=0.05)
    child = Child(name="A", current_age=14, cost_profile=profile, start_age=18, attendance_years=4)
    assumptions = Assumptions(expected_return_nominal=0.07, general_inflation=0.03)
    result = project_child_plan(child, assumptions)
    s = to_json(result)
    parsed = json.loads(s)
    assert parsed["child_name"] == "A"
    assert isinstance(parsed["schedule"], list)
