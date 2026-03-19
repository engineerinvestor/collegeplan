# Cost Profiles

A `CostProfile` defines the base annual cost and annual cost growth rate for a college education.

## Built-in profiles

Three factory functions create common cost profiles:

| Function | Base cost | Annual growth |
|---|---|---|
| `make_private_school_profile()` | $65,000 | 5.0% |
| `make_public_instate_profile()` | $28,000 | 4.0% |
| `make_public_oos_profile()` | $45,000 | 4.5% |

```python
from collegeplan import make_private_school_profile, make_public_instate_profile

private = make_private_school_profile()
public = make_public_instate_profile()
```

## Custom profiles

Create a `CostProfile` directly for any institution:

```python
from collegeplan import CostProfile

community_college = CostProfile(
    annual_cost=12_000,
    annual_cost_growth=0.03,
)
```

## How costs are projected

The engine grows the base annual cost by the `annual_cost_growth` rate each year from the child's current age to each year of attendance. For example, if a 5-year-old has a profile with $28,000 base cost and 4% growth, the cost at age 18 (13 years later) is:

```
$28,000 x (1.04)^13 = $46,214
```

Total projected cost is the sum across all attendance years.
