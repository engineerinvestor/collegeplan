# API Reference

The `collegeplan` package is organized into the following modules:

| Module | Description |
|---|---|
| [models](models.md) | Domain dataclasses: Child, Assumptions, CostProfile, results |
| [engine](engine.md) | Year-by-year projection functions |
| [solver](solver.md) | Bisection solver for required savings |
| [sensitivity](sensitivity.md) | Grid sweep across assumption parameters |
| [reporting](reporting.md) | Dict and JSON serialization |
| [cost_profiles](cost-profiles.md) | Built-in cost profile factories |
| [glide_path](glide-paths.md) | Age-based equity allocation and presets |
| [allocation](allocation.md) | Shared fund allocation policies |
| [assumptions](assumptions.md) | Fisher equation and return normalization |
| [validators](validators.md) | Input validation |
| [exceptions](exceptions.md) | Custom exception hierarchy |
