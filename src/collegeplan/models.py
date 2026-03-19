"""Domain models for college cost planning.

All models are frozen dataclasses — immutable, hashable, and lightweight.
Dollar amounts are floats; rounding to whole dollars happens at output boundaries.
Rates are stored as decimals (e.g., 0.05 not 5).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class AllocationPolicy(enum.Enum):
    """How a shared household fund is distributed among children."""

    EQUAL_SPLIT = "equal_split"
    OLDEST_FIRST = "oldest_first"
    PROPORTIONAL_TO_NEED = "proportional_to_need"


class ContributionTiming(enum.Enum):
    """When annual contributions are credited within each year."""

    END_OF_YEAR = "end_of_year"
    BEGINNING_OF_YEAR = "beginning_of_year"


# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True, kw_only=True)
class CostProfile:
    """Annual cost structure and growth assumptions for a school type."""

    label: str
    current_total_cost: float
    annual_cost_growth: float  # nominal rate, e.g. 0.05


@dataclass(frozen=True, slots=True, kw_only=True)
class GlidePathStep:
    """Asset allocation at a years-to-enrollment threshold."""

    years_to_enrollment: int  # upper bound (inclusive)
    equity_pct: float  # 0-1
    bond_pct: float  # 0-1
    short_term_pct: float  # 0-1


@dataclass(frozen=True, slots=True, kw_only=True)
class GlidePath:
    """Age-based asset allocation schedule with per-class return assumptions."""

    steps: tuple[GlidePathStep, ...]  # sorted descending by years_to_enrollment
    equity_return: float  # nominal expected return for equities
    bond_return: float  # nominal expected return for bonds
    short_term_return: float  # nominal expected return for cash/short-term


@dataclass(frozen=True, slots=True, kw_only=True)
class Child:
    """One future student and their per-child funding details."""

    name: str
    current_age: float
    cost_profile: CostProfile
    start_age: int = 18
    attendance_years: int = 4
    current_529_balance: float = 0.0
    annual_contribution: float = 0.0
    contribution_growth_rate: float = 0.0  # annual growth rate for contributions
    scholarship_offset: float = 0.0  # current dollars, annual
    scholarship_pct: float = 0.0  # 0-1, applied after cost projection
    glide_path: GlidePath | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class HouseholdFund:
    """Pooled assets not earmarked to a specific child."""

    shared_balance: float = 0.0
    shared_annual_contribution: float = 0.0
    contribution_growth_rate: float = 0.0  # annual growth rate for contributions
    allocation_policy: AllocationPolicy = AllocationPolicy.EQUAL_SPLIT


@dataclass(frozen=True, slots=True, kw_only=True)
class Assumptions:
    """Return, inflation, and timing assumptions for projections."""

    expected_return_nominal: float | None = None
    expected_return_real: float | None = None
    general_inflation: float = 0.03
    use_real_dollar_reporting: bool = False
    contribution_timing: ContributionTiming = ContributionTiming.END_OF_YEAR


# ---------------------------------------------------------------------------
# Output models
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True, kw_only=True)
class YearRecord:
    """One row of the annual projection schedule."""

    year_offset: int
    child_age: float
    beginning_balance: float
    contribution: float
    growth: float
    withdrawal: float
    ending_balance: float
    projected_cost: float


@dataclass(frozen=True, slots=True, kw_only=True)
class ChildProjectionResult:
    """Projection results for a single child."""

    child_name: str
    years_until_start: int
    projected_first_year_cost: float
    projected_total_cost: float
    funded_amount: float
    shortfall: float
    funded_ratio: float
    required_annual_savings: float
    required_monthly_savings: float
    schedule: tuple[YearRecord, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class HouseholdProjectionResult:
    """Projection results across all children in a household."""

    child_results: tuple[ChildProjectionResult, ...]
    total_projected_spend: float
    total_current_balances: float
    total_shortfall: float
    peak_annual_withdrawal: float
    overlap_years: tuple[int, ...]
    concurrent_enrollment_by_year: dict[int, int]
    schedule: tuple[YearRecord, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class SavingsSolution:
    """Result from the required-savings solver."""

    required_annual_contribution: float
    required_monthly_contribution: float
    per_child_suggestions: dict[str, float]
    achieved_funding_ratio: float


@dataclass(frozen=True, slots=True, kw_only=True)
class SensitivityCase:
    """One scenario within a sensitivity analysis."""

    parameters: dict[str, float]
    savings_solution: SavingsSolution | None = None
    household_result: HouseholdProjectionResult | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class SensitivityResult:
    """Collection of scenario results from a sensitivity sweep."""

    scenarios: tuple[SensitivityCase, ...]
