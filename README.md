# collegeplan

A pure-Python, zero-dependency college cost projection and savings planning engine.

## Install

```bash
pip install -e .
```

## Quick Start

### Project costs for one child

```python
from collegeplan import (
    Child, Assumptions, project_child_plan,
    make_private_school_profile, to_dict,
)

child = Child(
    name="Alice",
    current_age=5,
    cost_profile=make_private_school_profile(),  # $65k, 5% growth
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

### Project a household with multiple children

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

### Solve for required savings

```python
from collegeplan import solve_required_savings

solution = solve_required_savings(children, assumptions, shared)
print(f"Save ${solution.required_monthly_contribution:,.0f}/month to fully fund")
```

### Run a sensitivity sweep

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

## Key Concepts

All projections use **annual time steps** in **nominal dollars**. Rates are decimals (0.05, not 5). All domain models are **frozen dataclasses** — use `dataclasses.replace()` to create modified copies. The Fisher equation converts between real and nominal returns via `normalize_assumptions()`. Use `deflate()` to convert nominal projections to today's dollars.

## API Reference

**Core functions:**
- `project_child_plan(child, assumptions)` — project costs and funding for one child
- `project_household_plan(children, assumptions, household_fund)` — project across all children with optional shared pool
- `solve_required_savings(children, assumptions, ...)` — find the annual contribution needed to hit a funding target
- `run_sensitivity(children, assumptions, grid, ...)` — sweep across assumption/cost dimensions

**Profile factories:**
- `make_private_school_profile()` — $65k/yr, 5% growth
- `make_public_instate_profile()` — $28k/yr, 4% growth
- `make_public_oos_profile()` — $45k/yr, 4.5% growth

**Reporting:**
- `to_dict(result)` — serialize any result dataclass to a JSON-compatible dict (dollars rounded)
- `to_json(result)` — serialize to a JSON string

**Helpers:**
- `normalize_assumptions(assumptions)` — populate both nominal and real returns
- `deflate(nominal_value, years, inflation)` — convert future dollars to today's dollars

## Development

```bash
pip install -e ".[dev]"
pytest
pytest --cov=collegeplan
```
