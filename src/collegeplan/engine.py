"""Year-by-year projection engine for college cost planning."""

from __future__ import annotations

from dataclasses import replace

from .allocation import allocate_shared_withdrawal
from .assumptions import resolve_nominal_return
from .models import (
    Assumptions,
    Child,
    ChildProjectionResult,
    ContributionTiming,
    HouseholdFund,
    HouseholdProjectionResult,
    YearRecord,
)
from .validators import validate_assumptions, validate_child, validate_plan

# ---------------------------------------------------------------------------
# Cost projection helpers
# ---------------------------------------------------------------------------


def _project_annual_cost(child: Child, year_offset: int, inflation: float) -> float:
    """Project the net cost for a given year offset from today."""
    cp = child.cost_profile
    gross = cp.current_total_cost * (1 + cp.annual_cost_growth) ** year_offset

    if child.scholarship_pct > 0:
        gross *= 1 - child.scholarship_pct
    elif child.scholarship_offset > 0:
        offset_inflated = child.scholarship_offset * (1 + inflation) ** year_offset
        gross = max(0.0, gross - offset_inflated)

    return gross


def _years_until_start(child: Child) -> int:
    return max(0, int(child.start_age - child.current_age))


# ---------------------------------------------------------------------------
# Single-child projection
# ---------------------------------------------------------------------------


def project_child_plan(
    child: Child,
    assumptions: Assumptions,
) -> ChildProjectionResult:
    """Project costs and funding for a single child."""
    validate_child(child)
    validate_assumptions(assumptions)

    nominal_return = resolve_nominal_return(assumptions)
    inflation = assumptions.general_inflation
    years_to_start = _years_until_start(child)
    horizon = years_to_start + child.attendance_years

    # Build attendance year set (year offsets when child is in school)
    attendance_offsets = set(range(years_to_start, horizon))

    schedule: list[YearRecord] = []
    balance = child.current_529_balance
    total_cost = 0.0
    total_funded = 0.0
    first_year_cost = 0.0

    for y in range(horizon):
        beginning = balance
        cost = _project_annual_cost(child, y, inflation) if y in attendance_offsets else 0.0

        if y == years_to_start:
            first_year_cost = cost

        # Contribution and growth depend on timing
        if assumptions.contribution_timing == ContributionTiming.BEGINNING_OF_YEAR:
            contribution = child.annual_contribution
            growth = (beginning + contribution) * nominal_return
        else:
            growth = beginning * nominal_return
            contribution = child.annual_contribution

        available = beginning + growth + contribution
        withdrawal = min(cost, available)
        ending = available - withdrawal

        total_cost += cost
        total_funded += withdrawal

        schedule.append(
            YearRecord(
                year_offset=y,
                child_age=child.current_age + y,
                beginning_balance=beginning,
                contribution=contribution,
                growth=growth,
                withdrawal=withdrawal,
                ending_balance=ending,
                projected_cost=cost,
            )
        )
        balance = ending

    shortfall = max(0.0, total_cost - total_funded)
    funded_ratio = total_funded / total_cost if total_cost > 0 else 1.0

    return ChildProjectionResult(
        child_name=child.name,
        years_until_start=years_to_start,
        projected_first_year_cost=first_year_cost,
        projected_total_cost=total_cost,
        funded_amount=total_funded,
        shortfall=shortfall,
        funded_ratio=funded_ratio,
        required_annual_savings=0.0,  # populated by solver
        required_monthly_savings=0.0,
        schedule=tuple(schedule),
    )


# ---------------------------------------------------------------------------
# Household (multi-child) projection
# ---------------------------------------------------------------------------


def project_household_plan(
    children: list[Child],
    assumptions: Assumptions,
    household_fund: HouseholdFund | None = None,
) -> HouseholdProjectionResult:
    """Project costs and funding across all children in a household."""
    validate_plan(children, assumptions, household_fund)

    if household_fund is None:
        household_fund = HouseholdFund()

    nominal_return = resolve_nominal_return(assumptions)
    inflation = assumptions.general_inflation

    # Determine horizon
    horizon = max(
        _years_until_start(c) + c.attendance_years for c in children
    )

    # Sort children by years-to-start for priority ordering
    sorted_children = sorted(children, key=lambda c: _years_until_start(c))
    priority_order = [c.name for c in sorted_children]

    # Run per-child projections (without shared fund)
    child_results_no_shared = {
        c.name: project_child_plan(c, assumptions) for c in children
    }

    # Build per-child attendance schedule and cost lookup
    child_attendance: dict[str, set[int]] = {}
    child_costs: dict[str, dict[int, float]] = {}
    for c in children:
        yts = _years_until_start(c)
        offsets = set(range(yts, yts + c.attendance_years))
        child_attendance[c.name] = offsets
        child_costs[c.name] = {}
        for y in offsets:
            child_costs[c.name][y] = _project_annual_cost(c, y, inflation)

    # Simulate shared fund year-by-year
    shared_balance = household_fund.shared_balance
    shared_schedule: list[YearRecord] = []

    # Track per-child funded amounts from shared pool
    shared_funded: dict[str, float] = {c.name: 0.0 for c in children}

    for y in range(horizon):
        beginning = shared_balance

        if assumptions.contribution_timing == ContributionTiming.BEGINNING_OF_YEAR:
            contrib = household_fund.shared_annual_contribution
            growth = (beginning + contrib) * nominal_return
        else:
            growth = beginning * nominal_return
            contrib = household_fund.shared_annual_contribution

        available = beginning + growth + contrib

        # Determine per-child shortfalls from their own accounts this year
        child_needs: dict[str, float] = {}
        for c in children:
            cost_this_year = child_costs[c.name].get(y, 0.0)
            if cost_this_year <= 0:
                child_needs[c.name] = 0.0
                continue
            # What the child's own account covers this year
            own_result = child_results_no_shared[c.name]
            own_withdrawal = 0.0
            for rec in own_result.schedule:
                if rec.year_offset == y:
                    own_withdrawal = rec.withdrawal
                    break
            child_needs[c.name] = max(0.0, cost_this_year - own_withdrawal)

        total_need = sum(child_needs.values())
        if total_need > 0 and available > 0:
            allocs = allocate_shared_withdrawal(
                household_fund.allocation_policy,
                min(available, total_need),
                child_needs,
                priority_order,
            )
            total_withdrawal = sum(allocs.values())
            for name, amount in allocs.items():
                shared_funded[name] += amount
        else:
            total_withdrawal = 0.0

        ending = available - total_withdrawal
        shared_schedule.append(
            YearRecord(
                year_offset=y,
                child_age=0,  # not applicable for shared fund
                beginning_balance=beginning,
                contribution=contrib,
                growth=growth,
                withdrawal=total_withdrawal,
                ending_balance=ending,
                projected_cost=total_need,
            )
        )
        shared_balance = ending

    # Rebuild child results incorporating shared fund contributions
    final_child_results: list[ChildProjectionResult] = []
    for c in children:
        base = child_results_no_shared[c.name]
        extra_funded = shared_funded[c.name]
        total_funded = base.funded_amount + extra_funded
        total_cost = base.projected_total_cost
        shortfall = max(0.0, total_cost - total_funded)
        funded_ratio = total_funded / total_cost if total_cost > 0 else 1.0
        final_child_results.append(
            replace(
                base,
                funded_amount=total_funded,
                shortfall=shortfall,
                funded_ratio=funded_ratio,
            )
        )

    # Compute overlap metadata
    concurrent: dict[int, int] = {}
    for y in range(horizon):
        count = sum(1 for c in children if y in child_attendance[c.name])
        if count > 0:
            concurrent[y] = count
    overlap_years = tuple(y for y, count in concurrent.items() if count > 1)

    # Peak annual withdrawal across all sources
    peak_withdrawal = 0.0
    for y in range(horizon):
        year_total = sum(
            rec.withdrawal
            for cr in final_child_results
            for rec in cr.schedule
            if rec.year_offset == y
        ) + (shared_schedule[y].withdrawal if y < len(shared_schedule) else 0.0)
        peak_withdrawal = max(peak_withdrawal, year_total)

    total_spend = sum(cr.projected_total_cost for cr in final_child_results)
    total_balances = sum(c.current_529_balance for c in children) + household_fund.shared_balance
    total_shortfall = sum(cr.shortfall for cr in final_child_results)

    return HouseholdProjectionResult(
        child_results=tuple(final_child_results),
        total_projected_spend=total_spend,
        total_current_balances=total_balances,
        total_shortfall=total_shortfall,
        peak_annual_withdrawal=peak_withdrawal,
        overlap_years=overlap_years,
        concurrent_enrollment_by_year=concurrent,
        schedule=tuple(shared_schedule),
    )
