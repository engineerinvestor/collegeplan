"""Command-line interface for collegeplan."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .engine import project_household_plan
from .exceptions import CollegePlanError
from .models import (
    AllocationPolicy,
    Assumptions,
    Child,
    ContributionTiming,
    CostProfile,
    GlidePath,
    GlidePathStep,
    HouseholdFund,
)
from .reporting import to_dict
from .sensitivity import run_sensitivity
from .solver import solve_required_savings


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML plan file, returning the parsed dict."""
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        print(
            "PyYAML is required for the CLI. Install it with: pip install 'collegeplan[cli]'",
            file=sys.stderr,
        )
        sys.exit(1)
    with open(path) as f:
        data: dict[str, Any] = yaml.safe_load(f)
    return data


def _build_cost_profile(data: dict[str, Any]) -> CostProfile:
    """Build a CostProfile from a YAML dict."""
    return CostProfile(
        label=str(data.get("label", "Custom")),
        current_total_cost=float(data["current_total_cost"]),
        annual_cost_growth=float(data.get("annual_cost_growth", 0.04)),
    )


def _build_glide_path(data: dict[str, Any]) -> GlidePath:
    """Build a GlidePath from a YAML dict."""
    steps_data: list[dict[str, Any]] = data["steps"]
    steps = tuple(
        GlidePathStep(
            years_to_enrollment=int(s["years_to_enrollment"]),
            equity_pct=float(s["equity_pct"]),
            bond_pct=float(s["bond_pct"]),
            short_term_pct=float(s["short_term_pct"]),
        )
        for s in steps_data
    )
    return GlidePath(
        steps=steps,
        equity_return=float(data["equity_return"]),
        bond_return=float(data["bond_return"]),
        short_term_return=float(data["short_term_return"]),
    )


def _build_child(data: dict[str, Any]) -> Child:
    """Build a Child from a YAML dict."""
    cost_profile = _build_cost_profile(data["cost_profile"])
    glide_path = _build_glide_path(data["glide_path"]) if "glide_path" in data else None
    return Child(
        name=str(data["name"]),
        current_age=float(data["current_age"]),
        cost_profile=cost_profile,
        start_age=int(data.get("start_age", 18)),
        attendance_years=int(data.get("attendance_years", 4)),
        current_529_balance=float(data.get("current_529_balance", 0.0)),
        annual_contribution=float(data.get("annual_contribution", 0.0)),
        scholarship_offset=float(data.get("scholarship_offset", 0.0)),
        scholarship_pct=float(data.get("scholarship_pct", 0.0)),
        glide_path=glide_path,
    )


def _build_assumptions(data: dict[str, Any]) -> Assumptions:
    """Build Assumptions from a YAML dict."""
    timing_str = data.get("contribution_timing", "end_of_year")
    timing = ContributionTiming(timing_str)
    return Assumptions(
        expected_return_nominal=(
            float(data["expected_return_nominal"]) if "expected_return_nominal" in data else None
        ),
        expected_return_real=(
            float(data["expected_return_real"]) if "expected_return_real" in data else None
        ),
        general_inflation=float(data.get("general_inflation", 0.03)),
        use_real_dollar_reporting=bool(data.get("use_real_dollar_reporting", False)),
        contribution_timing=timing,
    )


def _build_household_fund(data: dict[str, Any]) -> HouseholdFund:
    """Build a HouseholdFund from a YAML dict."""
    policy_str = data.get("allocation_policy", "equal_split")
    policy = AllocationPolicy(policy_str)
    return HouseholdFund(
        shared_balance=float(data.get("shared_balance", 0.0)),
        shared_annual_contribution=float(data.get("shared_annual_contribution", 0.0)),
        allocation_policy=policy,
    )


def _parse_plan(
    data: dict[str, Any],
) -> tuple[
    list[Child],
    Assumptions,
    HouseholdFund | None,
]:
    """Parse a full plan file into domain objects."""
    assumptions = _build_assumptions(data["assumptions"])
    children = [_build_child(c) for c in data["children"]]
    household_fund = (
        _build_household_fund(data["household_fund"]) if "household_fund" in data else None
    )
    return children, assumptions, household_fund


def _cmd_project(args: argparse.Namespace) -> None:
    """Run a projection and print results."""
    data = _load_yaml(args.plan)
    children, assumptions, household_fund = _parse_plan(data)
    result = project_household_plan(children, assumptions, household_fund)
    output = to_dict(result)
    print(json.dumps(output, indent=2))


def _cmd_solve(args: argparse.Namespace) -> None:
    """Run the solver and print results."""
    data = _load_yaml(args.plan)
    children, assumptions, household_fund = _parse_plan(data)

    solve_opts = data.get("solve", {})
    target = float(solve_opts.get("target_funding_ratio", 1.0))
    mode = str(solve_opts.get("solve_mode", "child_level"))

    solution = solve_required_savings(
        children,
        assumptions,
        household_fund,
        target_funding_ratio=target,
        solve_mode=mode,
    )
    output = to_dict(solution)
    print(json.dumps(output, indent=2))


def _cmd_sensitivity(args: argparse.Namespace) -> None:
    """Run a sensitivity sweep and print results."""
    data = _load_yaml(args.plan)
    children, assumptions, household_fund = _parse_plan(data)

    sweep_opts = data.get("sensitivity", {})
    grid: dict[str, list[float]] = sweep_opts.get("grid", {})
    if not grid:
        print("No sensitivity grid found in plan file.", file=sys.stderr)
        sys.exit(1)

    target = float(sweep_opts.get("target_funding_ratio", 1.0))
    include_projection = bool(sweep_opts.get("include_projection", False))

    result = run_sensitivity(
        children,
        assumptions,
        grid,
        household_fund=household_fund,
        target_funding_ratio=target,
        include_projection=include_projection,
    )
    output = to_dict(result)
    print(json.dumps(output, indent=2))


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="collegeplan",
        description="College cost projection and savings planning engine",
    )
    subparsers = parser.add_subparsers(dest="command")

    project_parser = subparsers.add_parser(
        "project",
        help="Run a cost projection",
    )
    project_parser.add_argument("plan", type=Path, help="Path to YAML plan file")

    solve_parser = subparsers.add_parser(
        "solve",
        help="Solve for required annual savings",
    )
    solve_parser.add_argument("plan", type=Path, help="Path to YAML plan file")

    sensitivity_parser = subparsers.add_parser(
        "sensitivity",
        help="Run a sensitivity sweep",
    )
    sensitivity_parser.add_argument("plan", type=Path, help="Path to YAML plan file")

    return parser


def main(argv: list[str] | None = None) -> None:
    """Entry point for the CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "project":
            _cmd_project(args)
        elif args.command == "solve":
            _cmd_solve(args)
        elif args.command == "sensitivity":
            _cmd_sensitivity(args)
    except CollegePlanError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
