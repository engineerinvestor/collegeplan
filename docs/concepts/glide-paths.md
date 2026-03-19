# Glide Paths

A glide path defines how a child's 529 account allocation shifts between equities and bonds over time. This controls the blended investment return used each simulation year.

## How it works

A `GlidePath` is a list of `GlidePathStep` entries, each specifying an age and an equity fraction (0.0 to 1.0). The engine interpolates between steps to determine the equity allocation for any given age.

The blended return for each year is:

```
blended = equity_fraction x equity_return + (1 - equity_fraction) x bond_return
```

## Vanguard Target Enrollment preset

The `vanguard_target_enrollment()` function returns a glide path modeled after Vanguard's Target Enrollment funds:

```python
from collegeplan import vanguard_target_enrollment

glide = vanguard_target_enrollment()
```

This starts with a high equity allocation for young children and gradually shifts toward bonds as enrollment approaches.

## Custom glide paths

Create a custom glide path with `GlidePath` and `GlidePathStep`:

```python
from collegeplan import GlidePath, GlidePathStep

conservative = GlidePath(steps=[
    GlidePathStep(age=0, equity_fraction=0.60),
    GlidePathStep(age=10, equity_fraction=0.40),
    GlidePathStep(age=18, equity_fraction=0.10),
])
```

## Flat allocation

For a fixed allocation that does not change with age:

```python
from collegeplan import flat_equity_glide_path

# 80% equities at all ages
flat = flat_equity_glide_path(0.80)
```

## Using glide paths with children

Pass the glide path when creating a `Child`, along with equity and bond return assumptions:

```python
from collegeplan import Child, make_public_instate_profile, vanguard_target_enrollment

child = Child(
    name="Alice",
    current_age=5,
    cost_profile=make_public_instate_profile(),
    current_529_balance=25_000,
    annual_contribution=6_000,
    glide_path=vanguard_target_enrollment(),
)
```

When a glide path is set, the `Assumptions` must include `equity_return` and `bond_return` fields so the engine can compute the blended return for each year.
