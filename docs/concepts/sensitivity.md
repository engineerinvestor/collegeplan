# Sensitivity Analysis

Sensitivity analysis lets you stress-test a savings plan across a grid of assumptions, answering questions like "How much more would I need to save if returns are lower or costs grow faster?"

## Defining a grid

Pass a dictionary mapping assumption field names to lists of values:

```python
grid = {
    "expected_return_nominal": [0.05, 0.07, 0.09],
    "annual_cost_growth": [0.03, 0.05, 0.07],
}
```

This produces a Cartesian product of 3 x 3 = 9 scenarios.

## Running the sweep

```python
from collegeplan import run_sensitivity

sweep = run_sensitivity(children, assumptions, grid, household_fund=shared)
```

Each scenario in `sweep.scenarios` contains:

- `parameters`: the assumption values used for that scenario
- `savings_solution`: the `SavingsSolution` from the solver, including required annual and monthly contributions and the achieved funding ratio

## Interpreting results

```python
for case in sweep.scenarios:
    sol = case.savings_solution
    print(
        f"Return={case.parameters['expected_return_nominal']:.0%}, "
        f"Growth={case.parameters['annual_cost_growth']:.0%} → "
        f"${sol.required_monthly_contribution:,.0f}/mo"
    )
```

Look for scenarios where required savings jump significantly. These represent the assumptions your plan is most sensitive to.

## Supported parameters

Any numeric field on the `Assumptions` model or `annual_cost_growth` on cost profiles can be swept. Common choices:

- `expected_return_nominal` or `expected_return_real`
- `general_inflation`
- `annual_cost_growth`
