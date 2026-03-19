"""Shared fixtures for collegeplan tests."""

import pytest

from collegeplan import (
    Assumptions,
    Child,
    ContributionTiming,
    CostProfile,
)


@pytest.fixture
def simple_profile():
    """A cost profile with zero growth for hand-verifiable math."""
    return CostProfile(label="Test", current_total_cost=10_000, annual_cost_growth=0.0)


@pytest.fixture
def growing_profile():
    """A cost profile with 5% growth."""
    return CostProfile(label="Test Growing", current_total_cost=50_000, annual_cost_growth=0.05)


@pytest.fixture
def zero_return_assumptions():
    """Assumptions with 0% return and 0% inflation — pure arithmetic."""
    return Assumptions(expected_return_nominal=0.0, general_inflation=0.0)


@pytest.fixture
def nominal_assumptions():
    """Assumptions with 7% nominal return and 3% inflation."""
    return Assumptions(expected_return_nominal=0.07, general_inflation=0.03)


@pytest.fixture
def boy_assumptions():
    """Zero-return assumptions with beginning-of-year timing."""
    return Assumptions(
        expected_return_nominal=0.0,
        general_inflation=0.0,
        contribution_timing=ContributionTiming.BEGINNING_OF_YEAR,
    )


@pytest.fixture
def simple_child(simple_profile):
    """A child starting at 18, currently 14, with zero-growth costs."""
    return Child(
        name="Alice",
        current_age=14,
        cost_profile=simple_profile,
        start_age=18,
        attendance_years=4,
        current_529_balance=0.0,
        annual_contribution=0.0,
    )


@pytest.fixture
def funded_child(simple_profile):
    """A child whose 529 already covers full costs (4 x $10k = $40k)."""
    return Child(
        name="Bob",
        current_age=14,
        cost_profile=simple_profile,
        start_age=18,
        attendance_years=4,
        current_529_balance=40_000.0,
        annual_contribution=0.0,
    )
