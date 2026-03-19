"""Tests for cost profile factory functions."""

from collegeplan import (
    CostProfile,
    make_private_school_profile,
    make_public_instate_profile,
    make_public_oos_profile,
)


class TestPrivateSchoolProfile:
    def test_defaults(self):
        p = make_private_school_profile()
        assert p.current_total_cost == 65_000
        assert p.annual_cost_growth == 0.05
        assert p.label == "Private (4-year)"

    def test_custom_cost(self):
        p = make_private_school_profile(current_total_cost=70_000)
        assert p.current_total_cost == 70_000
        assert p.annual_cost_growth == 0.05

    def test_custom_growth(self):
        p = make_private_school_profile(annual_cost_growth=0.06)
        assert p.current_total_cost == 65_000
        assert p.annual_cost_growth == 0.06

    def test_both_overrides(self):
        p = make_private_school_profile(current_total_cost=80_000, annual_cost_growth=0.03)
        assert p.current_total_cost == 80_000
        assert p.annual_cost_growth == 0.03

    def test_returns_cost_profile(self):
        p = make_private_school_profile()
        assert isinstance(p, CostProfile)


class TestPublicInstateProfile:
    def test_defaults(self):
        p = make_public_instate_profile()
        assert p.current_total_cost == 28_000
        assert p.annual_cost_growth == 0.04
        assert p.label == "Public In-State (4-year)"

    def test_custom_overrides(self):
        p = make_public_instate_profile(current_total_cost=30_000, annual_cost_growth=0.05)
        assert p.current_total_cost == 30_000
        assert p.annual_cost_growth == 0.05


class TestPublicOosProfile:
    def test_defaults(self):
        p = make_public_oos_profile()
        assert p.current_total_cost == 45_000
        assert p.annual_cost_growth == 0.045
        assert p.label == "Public Out-of-State (4-year)"

    def test_custom_overrides(self):
        p = make_public_oos_profile(current_total_cost=50_000, annual_cost_growth=0.04)
        assert p.current_total_cost == 50_000
        assert p.annual_cost_growth == 0.04
