"""Scenario sweep engine for sensitivity analysis."""

from __future__ import annotations

import itertools
from dataclasses import replace

from .engine import project_household_plan
from .models import (
    Assumptions,
    Child,
    HouseholdFund,
    SensitivityCase,
    SensitivityResult,
)
from .solver import solve_required_savings


def run_sensitivity(
    children: list[Child],
    assumptions: Assumptions,
    grid: dict[str, list[float]],
    household_fund: HouseholdFund | None = None,
    target_funding_ratio: float = 1.0,
    include_projection: bool = False,
) -> SensitivityResult:
    """Run a sensitivity sweep across assumption/cost dimensions.

    Args:
        children: List of children to plan for.
        assumptions: Base assumptions to vary.
        grid: Mapping of parameter names to lists of values to sweep.
            Supported keys:
            - "expected_return_nominal"
            - "expected_return_real"
            - "general_inflation"
            - "annual_cost_growth" (applied to all children)
            - "scholarship_pct" (applied to all children)
            - "target_funding_ratio"
        household_fund: Optional shared pool.
        target_funding_ratio: Default target if not varied in grid.
        include_projection: If True, include full household projection results.
    """
    param_names = list(grid.keys())
    param_values = list(grid.values())
    combos = list(itertools.product(*param_values))

    cases: list[SensitivityCase] = []

    for combo in combos:
        params = dict(zip(param_names, combo, strict=True))
        mod_assumptions = assumptions
        mod_children = list(children)
        mod_target = target_funding_ratio

        for key, value in params.items():
            if key in ("expected_return_nominal", "expected_return_real", "general_inflation"):
                if key == "expected_return_nominal":
                    mod_assumptions = replace(
                        mod_assumptions,
                        expected_return_nominal=value,
                        expected_return_real=None,
                    )
                elif key == "expected_return_real":
                    mod_assumptions = replace(
                        mod_assumptions,
                        expected_return_real=value,
                        expected_return_nominal=None,
                    )
                else:
                    mod_assumptions = replace(mod_assumptions, general_inflation=value)
            elif key == "annual_cost_growth":
                mod_children = [
                    replace(c, cost_profile=replace(c.cost_profile, annual_cost_growth=value))
                    for c in mod_children
                ]
            elif key == "scholarship_pct":
                mod_children = [
                    replace(c, scholarship_pct=value, scholarship_offset=0.0)
                    for c in mod_children
                ]
            elif key == "target_funding_ratio":
                mod_target = value

        solution = solve_required_savings(
            mod_children, mod_assumptions, household_fund,
            target_funding_ratio=mod_target,
        )

        household_result = None
        if include_projection:
            household_result = project_household_plan(
                mod_children, mod_assumptions, household_fund,
            )

        cases.append(
            SensitivityCase(
                parameters=params,
                savings_solution=solution,
                household_result=household_result,
            )
        )

    return SensitivityResult(scenarios=tuple(cases))
