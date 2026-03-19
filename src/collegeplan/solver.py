"""Required-savings solver using bisection root-finding."""

from __future__ import annotations

from dataclasses import replace

from .engine import project_child_plan, project_household_plan
from .exceptions import SolverError
from .models import (
    Assumptions,
    Child,
    HouseholdFund,
    SavingsSolution,
)
from .validators import validate_plan


def _cost_weights(children: list[Child], assumptions: Assumptions) -> dict[str, float]:
    """Compute per-child weights based on projected total cost."""
    costs: dict[str, float] = {}
    for c in children:
        result = project_child_plan(c, assumptions)
        costs[c.name] = result.projected_total_cost
    total = sum(costs.values())
    if total == 0:
        n = len(children)
        return {c.name: 1.0 / n for c in children}
    return {name: cost / total for name, cost in costs.items()}


def _run_with_contribution(
    children: list[Child],
    assumptions: Assumptions,
    household_fund: HouseholdFund | None,
    annual_contribution: float,
    solve_mode: str,
    weights: dict[str, float] | None = None,
) -> float:
    """Run a projection with a candidate contribution and return the funding ratio."""
    if solve_mode == "child_level":
        if weights is None:
            n = len(children)
            modified = [
                replace(c, annual_contribution=c.annual_contribution + annual_contribution / n)
                for c in children
            ]
        else:
            modified = [
                replace(
                    c,
                    annual_contribution=c.annual_contribution
                    + annual_contribution * weights[c.name],
                )
                for c in children
            ]
        hf = household_fund
    else:  # shared_pool
        modified = list(children)
        if household_fund is None:
            hf = HouseholdFund(shared_annual_contribution=annual_contribution)
        else:
            hf = replace(
                household_fund,
                shared_annual_contribution=(
                    household_fund.shared_annual_contribution + annual_contribution
                ),
            )

    result = project_household_plan(modified, assumptions, hf)

    total_cost = result.total_projected_spend
    if total_cost == 0:
        return 1.0
    total_funded = sum(cr.funded_amount for cr in result.child_results)
    return total_funded / total_cost


def solve_required_savings(
    children: list[Child],
    assumptions: Assumptions,
    household_fund: HouseholdFund | None = None,
    target_funding_ratio: float = 1.0,
    solve_mode: str = "child_level",
    tolerance: float = 1.0,
    max_iterations: int = 100,
) -> SavingsSolution:
    """Find the annual contribution needed to reach a target funding ratio.

    Args:
        children: List of children to plan for.
        assumptions: Return and inflation assumptions.
        household_fund: Optional shared pool.
        target_funding_ratio: Desired funding level (1.0 = fully funded).
        solve_mode: "child_level" distributes contribution among children
            weighted by projected cost, "shared_pool" adds it to the
            household fund.
        tolerance: Convergence tolerance in dollars.
        max_iterations: Maximum bisection iterations.
    """
    validate_plan(children, assumptions, household_fund)

    # Compute cost-based weights for child_level distribution
    weights = _cost_weights(children, assumptions) if solve_mode == "child_level" else None

    # Check if already funded with zero additional contribution
    current_ratio = _run_with_contribution(
        children, assumptions, household_fund, 0.0, solve_mode, weights
    )
    if current_ratio >= target_funding_ratio:
        return SavingsSolution(
            required_annual_contribution=0.0,
            required_monthly_contribution=0.0,
            per_child_suggestions={c.name: 0.0 for c in children},
            achieved_funding_ratio=current_ratio,
        )

    # Establish upper bound
    total_cost = sum(
        c.cost_profile.current_total_cost
        * (1 + c.cost_profile.annual_cost_growth) ** int(c.start_age - c.current_age)
        * c.attendance_years
        for c in children
    )
    min_years = max(1, min(int(c.start_age - c.current_age) for c in children))
    upper = total_cost / min_years

    # Verify upper bound is sufficient
    upper_ratio = _run_with_contribution(
        children, assumptions, household_fund, upper, solve_mode, weights
    )
    while upper_ratio < target_funding_ratio:
        upper *= 2
        upper_ratio = _run_with_contribution(
            children, assumptions, household_fund, upper, solve_mode, weights
        )
        if upper > total_cost * 10:
            raise SolverError("Cannot find a feasible contribution within reasonable bounds")

    # Bisection
    lo, hi = 0.0, upper
    for _ in range(max_iterations):
        mid = (lo + hi) / 2
        ratio = _run_with_contribution(
            children, assumptions, household_fund, mid, solve_mode, weights
        )
        if ratio < target_funding_ratio:
            lo = mid
        else:
            hi = mid
        if hi - lo < tolerance:
            break
    else:
        raise SolverError(f"Solver did not converge after {max_iterations} iterations")

    annual = (lo + hi) / 2
    monthly = annual / 12

    if weights is not None:
        per_child = {c.name: annual * weights[c.name] for c in children}
    else:
        n = len(children)
        per_child = {c.name: annual / n for c in children}

    # Verify achieved ratio
    achieved = _run_with_contribution(
        children, assumptions, household_fund, annual, solve_mode, weights
    )

    return SavingsSolution(
        required_annual_contribution=annual,
        required_monthly_contribution=monthly,
        per_child_suggestions=per_child,
        achieved_funding_ratio=achieved,
    )
