# Installation

## From PyPI

```bash
pip install collegeplan
```

## Editable install (development)

Clone the repository and install in editable mode with dev dependencies:

```bash
git clone https://github.com/engineerinvestor/collegeplan.git
cd collegeplan
pip install -e ".[dev]"
```

## Optional dependencies

### Documentation

To build the documentation site locally:

```bash
pip install -e ".[docs]"
mkdocs serve
```

### Development tools

The `dev` extra includes:

- **pytest** and **pytest-cov** for testing
- **ruff** for linting and formatting
- **mypy** for type checking

## Requirements

- Python 3.11 or later
- No runtime dependencies (pure Python standard library)
