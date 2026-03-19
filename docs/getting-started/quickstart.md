# Quickstart

This guide walks through four common use cases. All examples assume you have installed `collegeplan`.

## Project costs for one child

Create a `Child` with a cost profile and run a projection:

```python
from collegeplan import (
    Child, Assumptions, project_child_plan,
    make_private_school_profile, to_dict,
)

child = Child(
    name="Alice",
    current_age=5,
    cost_profile=make_private_school_profile(),  # $65k/yr, 5% growth
    start_age=18,
    attendance_years=4,
    current_529_balance=25_000,
    annual_contribution=6_000,
)
assumptions = Assumptions(expected_return_nominal=0.07, general_inflation=0.03)

result = project_child_plan(child, assumptions)
print(f"Total cost: ${result.projected_total_cost:,.0f}")
print(f"Funded: {result.funded_ratio:.1%}")
```

The `result` is a `ChildProjectionResult` containing year-by-year records, total projected cost, total withdrawals, shortfall, and the funding ratio.

Use `to_dict(result)` to serialize to a JSON-compatible dictionary with rounded dollar amounts.

## Project a household with multiple children

When you have multiple children, use `project_household_plan()` with a shared `HouseholdFund`:

```python
from collegeplan import (
    Child, Assumptions, HouseholdFund, AllocationPolicy,
    project_household_plan, make_public_instate_profile,
)

children = [
    Child(name="Alice", current_age=10, cost_profile=make_public_instate_profile(),
          current_529_balance=15_000, annual_contribution=3_000),
    Child(name="Bob", current_age=7, cost_profile=make_public_instate_profile(),
          current_529_balance=8_000, annual_contribution=3_000),
]
assumptions = Assumptions(expected_return_nominal=0.07, general_inflation=0.03)
shared = HouseholdFund(
    shared_balance=20_000,
    shared_annual_contribution=5_000,
    allocation_policy=AllocationPolicy.PROPORTIONAL_TO_NEED,
)

result = project_household_plan(children, assumptions, shared)
for cr in result.child_results:
    print(f"{cr.child_name}: funded {cr.funded_ratio:.1%}, shortfall ${cr.shortfall:,.0f}")
```

The `allocation_policy` controls how the shared pool covers per-child shortfalls. Options are `EQUAL_SPLIT`, `OLDEST_FIRST`, and `PROPORTIONAL_TO_NEED`.

## Solve for required savings

Find the annual contribution needed to fully fund all children:

```python
from collegeplan import solve_required_savings

solution = solve_required_savings(children, assumptions, shared)
print(f"Save ${solution.required_monthly_contribution:,.0f}/month to fully fund")
```

The solver uses bisection to find the contribution level that achieves a 100% funding ratio (configurable via `target_funding_ratio`).

## Run a sensitivity sweep

Test your plan across a grid of assumptions:

```python
from collegeplan import run_sensitivity

grid = {
    "expected_return_nominal": [0.05, 0.07, 0.09],
    "annual_cost_growth": [0.03, 0.05, 0.07],
}
sweep = run_sensitivity(children, assumptions, grid, household_fund=shared)
for case in sweep.scenarios:
    sol = case.savings_solution
    print(f"Return={case.parameters['expected_return_nominal']:.0%}, "
          f"Growth={case.parameters['annual_cost_growth']:.0%} → "
          f"${sol.required_monthly_contribution:,.0f}/mo")
```

This produces a Cartesian product of all parameter combinations, solving for required savings in each scenario.
