# Overview

This page explains the core design decisions behind the `collegeplan` engine.

## Annual time steps

The engine simulates year-by-year, not monthly. Each simulation year applies contributions, investment growth, and (during college years) withdrawals. Monthly savings targets are derived as `annual / 12`.

## Nominal dollars

All projections run in nominal (future) dollars internally. This means projected costs reflect expected inflation and cost growth. To convert any nominal value back to today's purchasing power, use the `deflate()` helper:

```python
from collegeplan import deflate

# What is $100,000 in 13 years worth in today's dollars at 3% inflation?
real_value = deflate(100_000, years=13, inflation=0.03)
```

## Fisher equation

The engine uses the Fisher equation to convert between real and nominal returns:

```
(1 + nominal) = (1 + real) x (1 + inflation)
```

When you create `Assumptions`, provide exactly one of `expected_return_nominal` or `expected_return_real`. The `normalize_assumptions()` function computes the other using the Fisher equation and the `general_inflation` rate.

## Frozen dataclasses

All domain models (`Child`, `Assumptions`, `CostProfile`, etc.) are frozen dataclasses with `slots=True`. This means instances are immutable after creation. To create a modified copy, use `dataclasses.replace()`:

```python
import dataclasses
from collegeplan import Assumptions

base = Assumptions(expected_return_nominal=0.07, general_inflation=0.03)
optimistic = dataclasses.replace(base, expected_return_nominal=0.09)
```

## Withdrawal capping

During college years, if a child's 529 account cannot cover the full year's cost, the withdrawal is capped at the available balance. The remainder becomes explicit shortfall. Account balances never go negative.

## Household projection

The household projection runs in two phases:

1. Per-child projections run first (without the shared fund).
2. The shared pool is simulated year-by-year, allocating funds to cover per-child shortfalls according to the chosen `AllocationPolicy`.

See [Cost Profiles](cost-profiles.md), [Glide Paths](glide-paths.md), and [Sensitivity Analysis](sensitivity.md) for more details on specific features.
