# collegeplan

A pure-Python, zero-dependency college cost projection and savings planning engine.

## Features

- **Cost projection**: year-by-year college cost projections in nominal dollars
- **Multi-child households**: shared funding pools with configurable allocation policies
- **Savings solver**: bisection root-finder to determine required monthly contributions
- **Sensitivity analysis**: sweep across assumption grids to stress-test your plan
- **Built-in profiles**: private school, public in-state, and public out-of-state cost profiles
- **Glide paths**: age-based equity allocation with Vanguard Target Enrollment preset
- **Type-safe**: frozen dataclasses, strict mypy, PEP 561 typed marker
- **Zero dependencies**: pure Python standard library only

## Install

```bash
pip install collegeplan
```

## Quick example

```python
from collegeplan import (
    Child, Assumptions, project_child_plan,
    make_private_school_profile,
)

child = Child(
    name="Alice",
    current_age=5,
    cost_profile=make_private_school_profile(),
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

## Next steps

- [Installation](getting-started/installation.md): detailed install options
- [Quickstart](getting-started/quickstart.md): four worked examples
- [Concepts](concepts/overview.md): how the engine works
- [API Reference](api/index.md): full module documentation
