# collegeplan

[![CI](https://github.com/engineerinvestor/collegeplan/actions/workflows/ci.yml/badge.svg)](https://github.com/engineerinvestor/collegeplan/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/collegeplan)](https://pypi.org/project/collegeplan/)
[![Python](https://img.shields.io/pypi/pyversions/collegeplan)](https://pypi.org/project/collegeplan/)
[![License](https://img.shields.io/github/license/engineerinvestor/collegeplan)](LICENSE)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://engineerinvestor.github.io/collegeplan/)
[![Downloads](https://img.shields.io/pypi/dm/collegeplan)](https://pypi.org/project/collegeplan/)

A pure-Python, zero-dependency college cost projection and savings planning engine.

## Install

```bash
pip install collegeplan
```

## Quick Start

```python
from collegeplan import (
    Child, Assumptions, project_child_plan,
    make_private_school_profile,
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

## Documentation

Full documentation is available at [engineerinvestor.github.io/collegeplan](https://engineerinvestor.github.io/collegeplan/).

## Development

```bash
pip install -e ".[dev]"
pytest
pytest --cov=collegeplan
ruff check src/ tests/
mypy src/collegeplan/
```

## License

Apache 2.0. See [LICENSE](LICENSE) for details.
