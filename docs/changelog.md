# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-03-18

### Added

- Year-by-year college cost projection engine in nominal dollars.
- Single-child projection via `project_child_plan()`.
- Multi-child household projection with shared funding pool via `project_household_plan()`.
- Bisection solver to find required annual savings via `solve_required_savings()`.
- Sensitivity sweep across assumption grids via `run_sensitivity()`.
- Three built-in cost profiles: private school, public in-state, public out-of-state.
- Age-based glide path support with Vanguard Target Enrollment preset.
- Shared fund allocation policies: EQUAL_SPLIT, OLDEST_FIRST, PROPORTIONAL_TO_NEED.
- Fisher equation for real/nominal return conversion via `normalize_assumptions()`.
- `deflate()` helper for converting nominal projections to today's dollars.
- JSON and dict serialization via `to_dict()` and `to_json()`.
- Comprehensive input validation with descriptive error messages.
- Frozen dataclass models with `slots=True` for all domain objects.
- PEP 561 `py.typed` marker for type checker support.
- Full test suite (63 tests) with strict mypy and ruff linting.

[0.1.0]: https://github.com/engineerinvestor/collegeplan/releases/tag/v0.1.0
