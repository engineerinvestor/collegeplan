"""Tests for reporting/serialization."""

import json
from unittest import mock

import pytest

from collegeplan import (
    Assumptions,
    Child,
    CostProfile,
    HouseholdFund,
    project_child_plan,
    project_household_plan,
    to_dict,
    to_json,
)
from collegeplan.models import SavingsSolution, SensitivityCase, SensitivityResult
from collegeplan.reporting import to_dataframe


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
        name="A",
        current_age=14,
        cost_profile=profile,
        start_age=18,
        attendance_years=4,
        current_529_balance=20_000,
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


# ---------------------------------------------------------------------------
# to_dataframe tests (gated on pandas availability)
# ---------------------------------------------------------------------------


class TestToDataFrame:
    @pytest.fixture(autouse=True)
    def _require_pandas(self):
        pytest.importorskip("pandas")

    def _make_child_result(self):
        profile = CostProfile(label="T", current_total_cost=10_000, annual_cost_growth=0.0)
        child = Child(
            name="A",
            current_age=14,
            cost_profile=profile,
            start_age=18,
            attendance_years=4,
            current_529_balance=20_000,
        )
        assumptions = Assumptions(expected_return_nominal=0.0, general_inflation=0.0)
        return project_child_plan(child, assumptions)

    def test_to_dataframe_child(self):
        result = self._make_child_result()
        df = to_dataframe(result)
        assert len(df) == len(result.schedule)
        assert "year_offset" in df.columns
        assert "contribution" in df.columns
        assert "ending_balance" in df.columns

    def test_to_dataframe_household(self):
        profile = CostProfile(label="T", current_total_cost=10_000, annual_cost_growth=0.0)
        c1 = Child(name="A", current_age=14, cost_profile=profile, start_age=18, attendance_years=4)
        c2 = Child(name="B", current_age=16, cost_profile=profile, start_age=18, attendance_years=4)
        assumptions = Assumptions(expected_return_nominal=0.0, general_inflation=0.0)
        hf = HouseholdFund(shared_balance=10_000)
        result = project_household_plan([c1, c2], assumptions, hf)
        df = to_dataframe(result)
        assert "child_name" in df.columns
        names = set(df["child_name"].unique())
        assert "A" in names
        assert "B" in names
        assert "shared_fund" in names
        # Total rows = sum of child schedules + shared schedule
        expected_rows = sum(len(cr.schedule) for cr in result.child_results) + len(result.schedule)
        assert len(df) == expected_rows

    def test_to_dataframe_sensitivity(self):
        sol = SavingsSolution(
            required_annual_contribution=5000,
            required_monthly_contribution=416.67,
            per_child_suggestions={"A": 5000},
            achieved_funding_ratio=1.0,
        )
        case1 = SensitivityCase(
            parameters={"expected_return_nominal": 0.05},
            savings_solution=sol,
        )
        case2 = SensitivityCase(
            parameters={"expected_return_nominal": 0.08},
            savings_solution=sol,
        )
        result = SensitivityResult(scenarios=(case1, case2))
        df = to_dataframe(result)
        assert len(df) == 2
        assert "expected_return_nominal" in df.columns
        assert "required_annual_contribution" in df.columns
        assert "achieved_funding_ratio" in df.columns

    def test_to_dataframe_no_rounding(self):
        """Full float precision preserved in DataFrames."""
        result = self._make_child_result()
        df = to_dataframe(result)
        # Verify values are floats, not rounded ints
        for col in ["beginning_balance", "contribution", "growth", "ending_balance"]:
            assert df[col].dtype.kind == "f"


def test_to_dataframe_import_error():
    """Helpful error when pandas not installed."""
    with mock.patch.dict("sys.modules", {"pandas": None}):
        # Need to reload the module to trigger the import error
        import importlib

        import collegeplan.reporting as rep_mod

        importlib.reload(rep_mod)
        try:
            profile = CostProfile(label="T", current_total_cost=10_000, annual_cost_growth=0.0)
            child = Child(
                name="A",
                current_age=14,
                cost_profile=profile,
                start_age=18,
                attendance_years=4,
            )
            assumptions = Assumptions(expected_return_nominal=0.0, general_inflation=0.0)
            result = project_child_plan(child, assumptions)
            with pytest.raises(ImportError, match="pandas"):
                rep_mod.to_dataframe(result)
        finally:
            importlib.reload(rep_mod)
