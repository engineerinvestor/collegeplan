"""Input validation for collegeplan domain models."""

from __future__ import annotations

from .exceptions import ValidationError
from .models import Assumptions, Child, CostProfile, HouseholdFund


def validate_cost_profile(profile: CostProfile) -> None:
    if profile.current_total_cost <= 0:
        raise ValidationError("current_total_cost must be positive")
    if not -0.05 <= profile.annual_cost_growth <= 0.20:
        raise ValidationError(
            f"annual_cost_growth {profile.annual_cost_growth} is outside "
            "the plausible range [-0.05, 0.20]"
        )


def validate_child(child: Child) -> None:
    if child.current_age < 0 or child.current_age > 25:
        raise ValidationError(
            f"current_age {child.current_age} is outside [0, 25]"
        )
    if child.start_age < child.current_age:
        raise ValidationError(
            f"start_age {child.start_age} must be >= current_age {child.current_age}"
        )
    if not 1 <= child.attendance_years <= 6:
        raise ValidationError(
            f"attendance_years {child.attendance_years} is outside [1, 6]"
        )
    if child.current_529_balance < 0:
        raise ValidationError("current_529_balance must be non-negative")
    if child.annual_contribution < 0:
        raise ValidationError("annual_contribution must be non-negative")
    if child.scholarship_offset < 0:
        raise ValidationError("scholarship_offset must be non-negative")
    if not 0 <= child.scholarship_pct <= 1:
        raise ValidationError(
            f"scholarship_pct {child.scholarship_pct} is outside [0, 1]"
        )
    if child.scholarship_offset > 0 and child.scholarship_pct > 0:
        raise ValidationError(
            "Provide scholarship_offset or scholarship_pct, not both"
        )
    validate_cost_profile(child.cost_profile)


def validate_assumptions(assumptions: Assumptions) -> None:
    has_nominal = assumptions.expected_return_nominal is not None
    has_real = assumptions.expected_return_real is not None
    if not has_nominal and not has_real:
        raise ValidationError(
            "Provide expected_return_nominal or expected_return_real"
        )
    if has_nominal and has_real:
        raise ValidationError(
            "Provide expected_return_nominal or expected_return_real, not both"
        )
    if not -0.02 <= assumptions.general_inflation <= 0.15:
        raise ValidationError(
            f"general_inflation {assumptions.general_inflation} is outside "
            "the plausible range [-0.02, 0.15]"
        )


def validate_household_fund(fund: HouseholdFund) -> None:
    if fund.shared_balance < 0:
        raise ValidationError("shared_balance must be non-negative")
    if fund.shared_annual_contribution < 0:
        raise ValidationError("shared_annual_contribution must be non-negative")


def validate_plan(
    children: list[Child],
    assumptions: Assumptions,
    household_fund: HouseholdFund | None = None,
) -> None:
    """Validate all inputs for a projection or solver run."""
    if not children:
        raise ValidationError("At least one child is required")
    validate_assumptions(assumptions)
    for child in children:
        validate_child(child)
    if household_fund is not None:
        validate_household_fund(household_fund)
