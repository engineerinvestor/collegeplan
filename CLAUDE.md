# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A pure-Python, zero-dependency college cost projection and savings planning engine. It projects future college costs, simulates 529/savings account growth, solves for required savings via bisection, and runs sensitivity sweeps. Designed as a standalone library that can later be embedded into the Summitward product.

## Engineering Standards

- Python 3.10+
- Type hints on all functions
- `ruff` for linting and formatting, `mypy` for type checking
- `pytest` for testing with coverage
- Semantic versioning (v0.1 MVP → v0.5 → v1.0)

## Git Configuration

- **Remote:** https://github.com/engineerinvestor/lifecycle-allocation
- **Commit as:** Engineer Investor (`egr.investor@gmail.com`)
- Always use `git -c user.name="Engineer Investor" -c user.email="egr.investor@gmail.com" commit` when committing

## Writing Style

- **No em-dashes or double-dashes.** Never use `—` or `--` as punctuation in prose, markdown, or notebooks. Use a comma, period, colon, or semicolon instead.

## Commands

```bash
pip install -e ".[dev]"          # Install package + dev deps (pytest, pytest-cov, ruff, mypy)
pytest                            # Run all tests
pytest tests/test_engine.py       # Run one test file
pytest -k "test_name"             # Run a single test by name
pytest --cov=collegeplan          # Run with coverage
ruff check src/ tests/            # Lint (must pass clean)
ruff format --check src/ tests/   # Format check
mypy src/collegeplan/             # Type check (strict mode, must pass clean)
```

All code must pass `ruff check` and `mypy --strict` before committing. No CI pipeline exists yet.

### Ruff

Configured in `pyproject.toml`. Rules: E, F, W, I (isort), UP, B (bugbear), SIM, RUF. Line length 100. Target Python 3.11. `__all__` must be sorted (RUF022). Use `ruff check --fix` for auto-fixable issues.

### Mypy

Configured in `pyproject.toml` with `strict = true`. Covers `src/collegeplan/` only (not tests). All public functions need type annotations. Use `Any` sparingly and only where truly needed (e.g., serialization).

## Architecture

The package uses a `src/` layout (`src/collegeplan/`). All domain models are **frozen dataclasses** with `slots=True, kw_only=True`. Dollar amounts are `float` internally; rounding happens only at output boundaries. Rates are decimals (0.05, not 5).

### Data flow

```
Input models (Child, CostProfile, Assumptions, HouseholdFund)
  → validators.py (raises ValidationError on bad input)
  → assumptions.py (normalizes real/nominal returns via Fisher equation)
  → engine.py (year-by-year simulation producing ChildProjectionResult / HouseholdProjectionResult)
  → solver.py (bisection root-finder wrapping engine to solve for required annual savings)
  → sensitivity.py (Cartesian product sweep over assumption grid, calls solver per scenario)
  → reporting.py (dict/JSON serialization with dollar rounding)
```

### Key design decisions

- **Annual time steps.** The engine simulates year-by-year, not monthly. Monthly savings targets are derived as `annual / 12`.
- **Nominal dollars internally.** All projections run in nominal terms. Real-dollar conversions use `assumptions.deflate()`. The Fisher equation converts between real and nominal returns.
- **Immutable models.** Frozen dataclasses everywhere. Modifications use `dataclasses.replace()` to create new instances.
- **Withdrawal capping.** If a child's account can't cover a year's cost, the withdrawal is capped at available balance. The remainder becomes explicit shortfall (balances never go negative).
- **Household projection.** Runs per-child projections first (without shared fund), then simulates the shared pool year-by-year, allocating to cover per-child shortfalls via `allocation.py` policies (EQUAL_SPLIT, OLDEST_FIRST, PROPORTIONAL_TO_NEED).
- **Solver.** Bisection over a monotonic objective (more contribution = higher funding ratio). Upper bound is heuristically set then doubled until sufficient. Converges to $1 tolerance by default.
- **Assumptions must provide exactly one of** `expected_return_nominal` or `expected_return_real`, not both.

### Modules not yet implemented

- `cli.py`: YAML plan file loader and CLI (P1 scope)

## Spec Reference

`SPEC.md` is the authoritative requirements document. It defines the domain model fields, validation rules (section 14), calculation framework (section 8), public API signatures (section 9), output schemas (section 10), and MVP scope (section 22, P0/P1/P2).
