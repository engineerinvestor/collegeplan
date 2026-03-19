"""Tests for the CLI module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from collegeplan.cli import (
    _build_assumptions,
    _build_child,
    _build_cost_profile,
    _build_household_fund,
    _parse_plan,
    main,
)
from collegeplan.models import AllocationPolicy, ContributionTiming

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"


class TestBuildCostProfile:
    def test_minimal(self):
        data = {"current_total_cost": 50_000}
        cp = _build_cost_profile(data)
        assert cp.current_total_cost == 50_000
        assert cp.annual_cost_growth == 0.04
        assert cp.label == "Custom"

    def test_full(self):
        data = {"label": "Private", "current_total_cost": 65_000, "annual_cost_growth": 0.05}
        cp = _build_cost_profile(data)
        assert cp.label == "Private"
        assert cp.current_total_cost == 65_000
        assert cp.annual_cost_growth == 0.05


class TestBuildChild:
    def test_minimal(self):
        data = {
            "name": "Test",
            "current_age": 10,
            "cost_profile": {"current_total_cost": 30_000},
        }
        child = _build_child(data)
        assert child.name == "Test"
        assert child.current_age == 10
        assert child.start_age == 18
        assert child.attendance_years == 4
        assert child.current_529_balance == 0.0
        assert child.contribution_growth_rate == 0.0

    def test_with_all_fields(self):
        data = {
            "name": "Full",
            "current_age": 8,
            "start_age": 18,
            "attendance_years": 4,
            "current_529_balance": 25_000,
            "annual_contribution": 5_000,
            "scholarship_pct": 0.25,
            "cost_profile": {
                "label": "Public",
                "current_total_cost": 28_000,
                "annual_cost_growth": 0.04,
            },
        }
        child = _build_child(data)
        assert child.current_529_balance == 25_000
        assert child.scholarship_pct == 0.25

    def test_with_escalation(self):
        data = {
            "name": "Esc",
            "current_age": 8,
            "annual_contribution": 5_000,
            "contribution_growth_rate": 0.03,
            "cost_profile": {"current_total_cost": 30_000},
        }
        child = _build_child(data)
        assert child.contribution_growth_rate == 0.03


class TestBuildAssumptions:
    def test_nominal_return(self):
        data = {"expected_return_nominal": 0.07, "general_inflation": 0.03}
        a = _build_assumptions(data)
        assert a.expected_return_nominal == 0.07
        assert a.expected_return_real is None
        assert a.general_inflation == 0.03

    def test_real_return(self):
        data = {"expected_return_real": 0.04}
        a = _build_assumptions(data)
        assert a.expected_return_real == 0.04
        assert a.expected_return_nominal is None

    def test_contribution_timing(self):
        data = {
            "expected_return_nominal": 0.07,
            "contribution_timing": "beginning_of_year",
        }
        a = _build_assumptions(data)
        assert a.contribution_timing == ContributionTiming.BEGINNING_OF_YEAR


class TestBuildHouseholdFund:
    def test_defaults(self):
        data = {}
        hf = _build_household_fund(data)
        assert hf.shared_balance == 0.0
        assert hf.allocation_policy == AllocationPolicy.EQUAL_SPLIT

    def test_full(self):
        data = {
            "shared_balance": 20_000,
            "shared_annual_contribution": 5_000,
            "allocation_policy": "proportional_to_need",
        }
        hf = _build_household_fund(data)
        assert hf.shared_balance == 20_000
        assert hf.allocation_policy == AllocationPolicy.PROPORTIONAL_TO_NEED


class TestParsePlan:
    def test_minimal_plan(self):
        data = {
            "assumptions": {"expected_return_nominal": 0.07},
            "children": [
                {
                    "name": "Kid",
                    "current_age": 10,
                    "cost_profile": {"current_total_cost": 30_000},
                }
            ],
        }
        children, assumptions, hf = _parse_plan(data)
        assert len(children) == 1
        assert assumptions.expected_return_nominal == 0.07
        assert hf is None

    def test_plan_with_household_fund(self):
        data = {
            "assumptions": {"expected_return_nominal": 0.07},
            "children": [
                {
                    "name": "Kid",
                    "current_age": 10,
                    "cost_profile": {"current_total_cost": 30_000},
                }
            ],
            "household_fund": {"shared_balance": 10_000},
        }
        _children, _assumptions, hf = _parse_plan(data)
        assert hf is not None
        assert hf.shared_balance == 10_000


class TestCLICommands:
    """Smoke tests using example plan files."""

    @pytest.fixture(autouse=True)
    def _skip_without_yaml(self):
        pytest.importorskip("yaml")

    def test_project_command(self, capsys: pytest.CaptureFixture[str]):
        plan = EXAMPLES_DIR / "single_child.yaml"
        main(["project", str(plan)])
        output = json.loads(capsys.readouterr().out)
        assert "child_results" in output
        assert len(output["child_results"]) == 1

    def test_solve_command(self, capsys: pytest.CaptureFixture[str]):
        plan = EXAMPLES_DIR / "two_kids.yaml"
        main(["solve", str(plan)])
        output = json.loads(capsys.readouterr().out)
        assert "required_annual_contribution" in output
        assert "per_child_suggestions" in output
        assert output["required_annual_contribution"] >= 0

    def test_sensitivity_command(self, capsys: pytest.CaptureFixture[str]):
        plan = EXAMPLES_DIR / "sensitivity_sweep.yaml"
        main(["sensitivity", str(plan)])
        output = json.loads(capsys.readouterr().out)
        assert "scenarios" in output
        # 3 returns x 3 inflations = 9 scenarios
        assert len(output["scenarios"]) == 9

    def test_no_command_exits(self):
        with pytest.raises(SystemExit):
            main([])

    def test_solve_produces_valid_json(self, capsys: pytest.CaptureFixture[str]):
        plan = EXAMPLES_DIR / "single_child.yaml"
        main(["solve", str(plan)])
        output = capsys.readouterr().out
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_sensitivity_no_grid_exits(self, tmp_path: Path):
        plan = tmp_path / "no_grid.yaml"
        plan.write_text(
            "assumptions:\n"
            "  expected_return_nominal: 0.07\n"
            "children:\n"
            "  - name: Kid\n"
            "    current_age: 10\n"
            "    cost_profile:\n"
            "      current_total_cost: 30000\n"
        )
        with pytest.raises(SystemExit):
            main(["sensitivity", str(plan)])
