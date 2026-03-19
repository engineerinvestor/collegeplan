"""Tests for input validation rules."""

import pytest

from collegeplan import (
    Assumptions,
    Child,
    CostProfile,
    GlidePath,
    GlidePathStep,
    ValidationError,
    vanguard_target_enrollment,
)
from collegeplan.validators import (
    validate_assumptions,
    validate_child,
    validate_cost_profile,
    validate_glide_path,
)


def test_cost_profile_zero_cost():
    with pytest.raises(ValidationError, match="current_total_cost"):
        validate_cost_profile(CostProfile(label="X", current_total_cost=0, annual_cost_growth=0.03))


def test_cost_profile_growth_out_of_range():
    with pytest.raises(ValidationError, match="annual_cost_growth"):
        validate_cost_profile(
            CostProfile(label="X", current_total_cost=1000, annual_cost_growth=0.25)
        )


def test_child_age_negative():
    cp = CostProfile(label="X", current_total_cost=1000, annual_cost_growth=0.03)
    with pytest.raises(ValidationError, match="current_age"):
        validate_child(Child(name="A", current_age=-1, cost_profile=cp))


def test_child_start_before_current():
    cp = CostProfile(label="X", current_total_cost=1000, annual_cost_growth=0.03)
    with pytest.raises(ValidationError, match="start_age"):
        validate_child(Child(name="A", current_age=20, cost_profile=cp, start_age=18))


def test_child_attendance_years_zero():
    cp = CostProfile(label="X", current_total_cost=1000, annual_cost_growth=0.03)
    with pytest.raises(ValidationError, match="attendance_years"):
        validate_child(Child(name="A", current_age=10, cost_profile=cp, attendance_years=0))


def test_child_both_scholarships():
    cp = CostProfile(label="X", current_total_cost=1000, annual_cost_growth=0.03)
    with pytest.raises(ValidationError, match="scholarship"):
        validate_child(
            Child(
                name="A",
                current_age=10,
                cost_profile=cp,
                scholarship_offset=500,
                scholarship_pct=0.1,
            )
        )


def test_assumptions_neither_return():
    with pytest.raises(ValidationError, match="expected_return"):
        validate_assumptions(Assumptions())


def test_assumptions_both_returns():
    with pytest.raises(ValidationError, match="not both"):
        validate_assumptions(Assumptions(expected_return_nominal=0.07, expected_return_real=0.04))


def test_validate_glide_path_valid():
    """A valid Vanguard glide path passes validation."""
    gp = vanguard_target_enrollment()
    validate_glide_path(gp)  # should not raise


def test_validate_glide_path_bad_sum():
    """Percentages not summing to 1.0 raises ValidationError."""
    steps = (
        GlidePathStep(years_to_enrollment=18, equity_pct=0.5, bond_pct=0.1, short_term_pct=0.1),
    )
    gp = GlidePath(steps=steps, equity_return=0.10, bond_return=0.04, short_term_return=0.02)
    with pytest.raises(ValidationError, match="sum to"):
        validate_glide_path(gp)


def test_validate_glide_path_negative_pct():
    """Negative percentage raises ValidationError."""
    steps = (
        GlidePathStep(years_to_enrollment=18, equity_pct=-0.1, bond_pct=0.6, short_term_pct=0.5),
    )
    gp = GlidePath(steps=steps, equity_return=0.10, bond_return=0.04, short_term_return=0.02)
    with pytest.raises(ValidationError, match="outside"):
        validate_glide_path(gp)
