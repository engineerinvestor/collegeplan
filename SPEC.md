Below is a practical spec for a **standalone Python package** that projects college costs and required savings for one or more children. It is designed to be usable on its own today and cleanly embedded into **Summitward** later.

---

# Spec: Python Package for DIY College Cost Planning

## 1. Recommendation

I recommend building a package with a **small, deterministic core** and a **few high-value extensions**, rather than a giant “retirement-planner-for-college” system.

The right scope is:

* **Core engine** for projecting college costs and funding gaps
* Support for **multiple children**
* Support for **existing 529 balances**
* Ability to compute **required annual/monthly savings**
* Support for **real vs nominal assumptions**
* Support for **household-level overlap** when siblings attend college at the same time
* A simple **scenario/sensitivity engine**

I would **not** start with:

* live school data scraping
* tax-law-heavy logic
* brokerage syncing
* overly complex Monte Carlo as the main path
* a database or web framework dependency
* a UI inside the package

That would be too much for v1 and would make Summitward integration harder, not easier.

---

## 2. Product Goal

Help families estimate:

1. What college may cost for each child
2. How much they need to save each year or month
3. Whether they are currently on track
4. How multiple children change total household funding needs
5. What happens under different assumptions

The package should be good for:

* selective private school planning
* public in-state / out-of-state planning
* custom school assumptions
* “option value” planning even if the specific school is unknown

---

## 3. Design Principles

### A. Engine first, UI second

The package should be a **pure planning engine** with zero dependency on Summitward UI or storage.

Why:

* easier to test
* easier to reuse
* easier to version
* avoids coupling business logic to product logic

### B. Annual granularity for the core model

Use **annual time steps** internally.

Why:

* college planning is dominated by year-level assumptions
* much simpler than monthly cash-flow simulation
* good enough for planning accuracy

You can still return an equivalent “monthly savings target” for display.

### C. Deterministic first, stochastic second

Make deterministic planning the default. Add scenario sweeps immediately. Make Monte Carlo optional later.

Why:

* most users want understandable numbers first
* a deterministic model is easier to validate
* scenario analysis usually captures most of the value without overwhelming the user

### D. User-configurable assumptions

Do not hardcode a worldview. Make assumptions explicit and overridable.

Why:

* parents differ on school type, inflation, scholarships, and return expectations
* Summitward will likely want opinionated defaults later, but the package should stay neutral

---

## 4. Core Use Cases

### Primary use cases

* “I have one 2-year-old, $50k in a 529, what should I save annually?”
* “I have three kids ages 1, 4, and 7. What is my peak annual college burden?”
* “What if private school costs grow 2% faster than inflation?”
* “How much of my goal is already funded?”
* “How much do I need to save if I want 75% or 100% funding?”

### Secondary use cases

* compare public vs private planning targets
* compare equal contributions vs age-weighted contributions
* compare separate child accounts vs a shared family college fund

---

## 5. Non-Goals

The package should **not** initially do the following:

* determine actual financial aid awards
* optimize FAFSA/CSS strategies
* encode detailed 529 tax rules by state
* scrape current school sticker prices
* manage brokerage/529 accounts directly
* provide a web server, GUI, or persistence layer
* solve full retirement + college tradeoff optimization

Why not:

* these are either unstable, product-specific, or much more complex than the core value proposition

---

## 6. Package Scope

Suggested package name ideas:

* `collegeplan`
* `collegefund`
* `eduplan`
* `tuitionpath`

I would favor something generic and reusable like **`collegeplan`**.

---

## 7. Domain Model

## 7.1 Child

Represents one future student.

Fields:

* `name`
* `current_age_years`
* `start_age_years` (default 18)
* `attendance_years` (default 4)
* `school_type` or `cost_profile_id`
* `current_529_balance`
* `annual_contribution`
* `scholarship_offset_current_dollars` or percent
* `custom_start_year` optional

Why:

* this keeps child-specific assumptions isolated
* allows multiple children with different targets

## 7.2 Cost Profile

Defines the current annual cost structure and cost growth assumptions.

Fields:

* `label`
* `current_total_cost`
* optional breakout:

  * `tuition_and_fees`
  * `room_and_board`
  * `books_and_other`
* `annual_college_cost_growth_nominal`
* optional `growth_by_component`

Recommended v1:

* support either:

  * a single total COA growth rate, or
  * an optional component-level model

Why:

* single-rate model is enough for most users
* component-level inputs are useful but should stay optional

## 7.3 Household / Shared Funding Pool

Represents pooled assets not earmarked to a specific child.

Fields:

* `shared_college_balance`
* `shared_annual_contribution`
* `allocation_policy`

Recommended allocation policies:

* `equal_split`
* `oldest_first`
* `proportional_to_projected_need`

Why:

* many families use separate 529s, but many effectively think in household terms
* these three policies cover most reasonable planning behavior without overengineering

## 7.4 Return / Inflation Assumptions

Fields:

* `expected_return_nominal` or `expected_return_real`
* `general_inflation`
* `use_real_dollar_reporting` boolean
* `contribution_timing` (`end_of_year` default)

Why:

* users think in both real and nominal terms
* the package should normalize assumptions internally

---

## 8. Calculation Framework

## 8.1 Internal standard

I recommend the engine operate in **nominal annual dollars internally**, while allowing real-dollar inputs and outputs.

Why:

* college cost growth is naturally modeled nominally
* nominal projections are easier to explain for future sticker price
* real-dollar reporting can still be layered on top

If the user inputs a real return:
[
1 + r_{nominal} = (1 + r_{real})(1 + \pi)
]

If the user wants real-dollar reporting:
[
1 + g_{real_college} = \frac{1 + g_{college}}{1 + \pi} - 1
]

## 8.2 Cost projection

For each child:

1. Years until matriculation
2. Project first-year cost forward
3. Project years 2–4 with the same college inflation assumption
4. Apply scholarship/grant offsets if provided

## 8.3 Funding simulation

For each simulation year:

* grow beginning balances
* add annual contributions
* when a child starts school, withdraw that year’s projected cost
* allocate withdrawals from child-specific accounts first, then shared pool, or vice versa based on policy

This is best implemented as a **year-by-year simulator**, not a closed-form formula, because:

* multiple children overlap
* shared pools complicate algebra
* future Summitward integration will likely benefit from explicit schedules

## 8.4 Required savings solver

The package should solve for:

* required annual contribution
* equivalent monthly contribution
* required contribution per child
* required household contribution

Recommended solver:

* **bisection/root finding**

Why:

* simple
* robust
* monotonic problem
* easy to explain and test

---

## 9. Recommended Public API

The public API should be minimal and stable.

## 9.1 Core functions

### `project_child_plan(child, assumptions, cost_profile) -> ChildProjectionResult`

Returns:

* projected annual college costs
* projected account balances
* funding gap / surplus
* funded ratio

### `project_household_plan(children, household_fund, assumptions) -> HouseholdProjectionResult`

Returns:

* per-child results
* consolidated year-by-year funding schedule
* peak annual withdrawal burden
* total projected education spending
* final balances and shortfalls

### `solve_required_savings(children, household_fund, assumptions, target_funding_ratio=1.0) -> SavingsSolution`

Returns:

* required annual contribution
* equivalent monthly contribution
* optional child-level contribution suggestions

### `run_sensitivity(plan, grid) -> SensitivityResult`

Varies assumptions such as:

* return
* college inflation
* scholarship
* school type

Why:

* this is one of the highest-value features for planning confidence

## 9.2 Optional helpers

* `make_private_school_profile(...)`
* `make_public_instate_profile(...)`
* `make_public_oos_profile(...)`
* `to_dataframe(result)` as an optional pandas adapter
* `to_dict(result)` for API/UI integration

---

## 10. Output Objects

Each result object should include both summary fields and a schedule.

### Child result summary

* child name
* years until start
* projected first-year cost
* projected 4-year total cost
* funded amount
* shortfall amount
* funded ratio
* required annual savings
* required monthly savings

### Child yearly schedule

For each year:

* child age
* calendar year offset
* projected cost
* contribution
* beginning balance
* growth
* ending balance
* withdrawal

### Household summary

* total projected spend across all children
* total current balances
* total future contributions
* total shortfall/surplus
* peak annual withdrawal
* years with overlapping attendance
* number of concurrently enrolled children by year

This overlap view is especially important for families with 2+ kids.

---

## 11. Package Architecture

Recommended structure:

```text
src/collegeplan/
    __init__.py
    models.py
    validators.py
    assumptions.py
    cost_profiles.py
    engine.py
    allocation.py
    solver.py
    sensitivity.py
    reporting.py
    exceptions.py
    cli.py              # optional minimal CLI
tests/
docs/
pyproject.toml
README.md
```

### Module responsibilities

* `models.py`: dataclasses for plans, children, assumptions, results
* `validators.py`: input validation and normalization
* `cost_profiles.py`: standard profile builders
* `engine.py`: year-by-year projection logic
* `allocation.py`: shared-fund allocation policy logic
* `solver.py`: required savings root finder
* `sensitivity.py`: scenario sweeps
* `reporting.py`: dict/table-friendly conversion

---

## 12. Data Modeling Recommendation

I recommend using **frozen dataclasses** for the core models.

Why:

* lightweight
* standard library
* easy to understand
* stable dependency surface

I would **not** use a heavy ORM or web framework model layer.

I would also avoid making **Pydantic** a hard dependency in the core package unless you know you want JSON-heavy APIs from day one. Summitward can always wrap the package with Pydantic later.

---

## 13. Numeric Types

I recommend using **float** internally and rounding at output boundaries.

Why:

* college planning is not a cents-level accounting system
* floats make scenario analysis and optional Monte Carlo far easier
* `Decimal` tends to create friction without meaningful practical benefit here

Return final dollar outputs rounded to the nearest whole dollar unless the caller asks otherwise.

---

## 14. Validation Rules

The package should validate:

* non-negative costs and balances
* ages within a sensible range
* start age greater than or equal to current age
* attendance years between 1 and 6 unless overridden
* return and inflation assumptions not absurdly invalid
* allocation weights sum correctly if custom weights are later supported

Invalid inputs should raise clear typed exceptions.

---

## 15. Scenario Engine

A scenario engine should be part of v1.

Recommended scenario dimensions:

* expected return
* general inflation
* college inflation
* school type
* scholarship offset
* funding ratio target

Recommended output:

* low / base / high tables
* sensitivity matrix
* “required annual savings under each assumption set”

Why:

* users care more about assumption sensitivity than false precision

---

## 16. Monte Carlo Recommendation

I would make Monte Carlo a **Phase 2** feature, not the centerpiece of v1.

Why yes eventually:

* investment returns are uncertain
* useful for “probability of full funding”

Why not in v1:

* significantly more design complexity
* introduces distribution assumptions debates
* deterministic + scenario analysis gets most of the value sooner

If added later:

* put it in `monte_carlo.py`
* optional dependency on NumPy
* expose a simple probability-of-success output

---

## 17. CLI Recommendation

A small CLI is worth adding, but keep it thin.

Example commands:

* `collegeplan project plan.yaml`
* `collegeplan solve plan.yaml`
* `collegeplan sensitivity plan.yaml`

Why:

* useful for developers and power users
* makes the package feel standalone
* also useful for Summitward internal testing

Why not more:

* do not build a full terminal app
* CLI should just load config and print results

---

## 18. File Format Recommendation

Support:

* Python object API first
* JSON and YAML plan files second

Why:

* object API is best for Summitward integration
* YAML/JSON makes the package independently usable

A plan file should define:

* household assumptions
* cost profiles
* children
* shared fund settings

---

## 19. Summitward Integration Contract

Design the package as if Summitward will treat it as a versioned engine.

That means:

* no database dependency
* pure functions where possible
* stable result schemas
* serializable outputs
* semantic versioning
* no hidden globals

Best pattern:

* Summitward owns user profiles, UI, persistence, and assumption presets
* the package owns projection math

That is the right boundary.

---

## 20. Testing Strategy

You want strong deterministic tests.

### Unit tests

* single-child closed-form sanity cases
* zero-inflation cases
* zero-return cases
* immediate matriculation edge cases
* negative/invalid input handling
* shared-fund allocation policy behavior

### Integration tests

* 2–3 realistic family plans
* overlapping sibling attendance
* compare solver output to simulated funded ratio

### Golden tests

Keep fixed plan fixtures and expected outputs so refactors do not silently change results.

---

## 21. Documentation Requirements

The package should ship with:

* `README.md`
* assumptions glossary
* quickstart examples
* common planning recipes
* explanation of real vs nominal
* explanation of what is and is not modeled

Most important docs pages:

1. “Project one child”
2. “Project multiple children”
3. “Solve required savings”
4. “Run scenario analysis”
5. “Using this package inside another application”

---

## 22. Suggested MVP Scope

## P0: Must have

* child model
* cost profile model
* household/shared pool model
* deterministic annual projection engine
* required annual savings solver
* multi-child overlap support
* scenario sweeps
* dict/JSON-friendly outputs
* tests and docs

## P1: Nice next step

* YAML config loader
* CLI
* pandas export
* richer cost component modeling
* preset school profile templates

## P2: Later

* Monte Carlo success probability
* contribution escalation rules
* custom funding priority policies
* school data import adapters
* Summitward-specific wrappers

---

## 23. What I Would Explicitly Avoid

### Avoid school scraping in the package

Why not:

* stale, brittle, and product-specific
* better as a separate data ingestion layer

### Avoid encoding detailed aid formulas

Why not:

* too noisy and unstable for a generic library
* creates false confidence

### Avoid monthly simulation as the core engine

Why not:

* complexity gain is not worth it for this use case

### Avoid trying to combine full retirement planning from day one

Why not:

* different product boundary
* makes the package bloated

### Avoid a giant dependency graph

Why not:

* this should be easy to install and embed

---

## 24. Final Recommendation

Build this as a **focused planning engine**, not as a mini personal finance platform.

The best v1 is:

* **annual deterministic simulation**
* **multi-child support**
* **shared and per-child funding support**
* **required savings solver**
* **scenario analysis**
* **clean standalone API**

That is enough to be genuinely useful on its own and also the right size to become a reliable dependency for Summitward later.

If you want, I can turn this into a **GitHub-ready `SPEC.md` document** with acceptance criteria, class definitions, and example JSON/YAML schemas.


---

My recommendation: **use a hybrid approach**.

Keep the package **private during early 0.x development**, then **open-source the stable math/engine core** once the API settles. Keep the **Summitward-specific product layer proprietary**.

That is the best balance for this kind of tool.

## Why I would not keep the whole thing proprietary

For a college-cost planning package, the core value is mostly:

* transparent assumptions
* trustworthy math
* good defaults
* easy integration
* strong UX around the engine

The raw projection engine itself is **not likely to be your long-term moat**. In personal finance, openness can actually be an advantage because users are naturally skeptical of black-box calculators. If the core is open, it helps with:

**Trust.** People can inspect the formulas and assumptions.

**Credibility.** An open engine feels more serious and less “marketing calculator.”

**Distribution.** Developers, bloggers, and DIY finance folks may adopt it independently.

**Brand spillover.** Open source can feed Summitward awareness, GitHub discoverability, and your broader Engineer Investor / technical-finance brand.

**Reuse across products.** A clean open package is easier to test, document, and reuse internally too.

## Why I would not open-source everything

You do not want to give away the full product stack. The parts that are more plausibly defensible are:

* Summitward UX and workflows
* scenario presets and planning frameworks
* account/integration plumbing
* data pipelines
* recommendation layer
* future optimization logic across retirement + college + taxes
* premium reporting, dashboards, and collaboration features

That is where product value compounds.

If you open-source all of that, you risk taking on support burden and helping clones more than helping yourself.

## Why I would not open-source immediately

Early open-sourcing sounds noble, but there are real downsides when the design is still moving:

**API churn.** You will want freedom to rename models, change result schemas, and refactor solver logic.

**Support burden.** Even a small open-source repo can create issues, docs work, and maintenance expectations.

**Premature public surface area.** You may publish abstractions that you later regret.

**Licensing decisions become sticky.** It is easier to open later than to claw things back.

That is why I would start with a **private repo**, build until the boundary is clean, then release the core when it feels stable.

## What I would open-source

Once stable, I’d open-source:

* data models
* projection engine
* savings solver
* scenario engine
* basic cost-profile presets
* CLI or notebook examples
* serialization helpers

This makes the package genuinely useful on its own and builds trust.

## What I would keep proprietary

I’d keep closed:

* Summitward wrappers and internal adapters
* opinionated product defaults
* richer planning workflows
* cross-goal planning logic
* premium reporting and UX
* integrations and sync layers
* any future recommendation/ranking layer

## Best licensing posture

If you open-source the core, I would lean toward **Apache-2.0** over MIT.

Why:

* still permissive
* clearer patent language
* more “serious library” feel for a finance/planning engine

If your main concern is preventing direct commercial cloning, you could consider a **source-available** model instead, but that usually reduces adoption a lot. For a trust-building finance engine, I think permissive open source is usually the better play.

## Bottom line

I would **not** keep the whole thing proprietary.

I would also **not** rush to open it today.

I’d do this:

**Phase 1:** private while the API is unstable
**Phase 2:** open-source the core projection engine
**Phase 3:** keep Summitward product features, integrations, and premium planning layers proprietary

That gives you trust and distribution without giving away the product.

If you want, I’ll turn that into a concrete repo strategy with suggested package boundaries, license choice, and what lives in `collegeplan-core` vs Summitward.
