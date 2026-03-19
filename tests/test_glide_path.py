"""Tests for glide path asset allocation logic."""

import pytest

from collegeplan import (
    Assumptions,
    Child,
    CostProfile,
    blended_return,
    flat_equity_glide_path,
    get_return_for_year,
    vanguard_target_enrollment,
)
from collegeplan.assumptions import resolve_nominal_return


@pytest.fixture
def vanguard_gp():
    return vanguard_target_enrollment()


@pytest.fixture
def glide_child(vanguard_gp):
    profile = CostProfile(label="Test", current_total_cost=25_000, annual_cost_growth=0.04)
    return Child(
        name="G",
        current_age=10,
        cost_profile=profile,
        start_age=18,
        attendance_years=4,
        current_529_balance=10_000,
        glide_path=vanguard_gp,
    )


class TestBlendedReturn:
    def test_at_18_years(self, vanguard_gp):
        """At 18 years out, allocation is 95/5/0."""
        ret = blended_return(vanguard_gp, 18)
        expected = 0.95 * 0.10 + 0.05 * 0.04 + 0.0 * 0.02
        assert ret == pytest.approx(expected)

    def test_at_10_years(self, vanguard_gp):
        """At 10 years out, falls in the 11-year step (66.5/33.5/0)."""
        ret = blended_return(vanguard_gp, 10)
        expected = 0.665 * 0.10 + 0.335 * 0.04
        assert ret == pytest.approx(expected)

    def test_at_5_years(self, vanguard_gp):
        """At 5 years out, allocation is 32.3/56.0/11.7."""
        ret = blended_return(vanguard_gp, 5)
        expected = 0.323 * 0.10 + 0.560 * 0.04 + 0.117 * 0.02
        assert ret == pytest.approx(expected)

    def test_at_0_years(self, vanguard_gp):
        """At enrollment, allocation is 14.0/34.3/51.7."""
        ret = blended_return(vanguard_gp, 0)
        expected = 0.140 * 0.10 + 0.343 * 0.04 + 0.517 * 0.02
        assert ret == pytest.approx(expected)

    def test_negative_years(self, vanguard_gp):
        """Post-enrollment uses the smallest step with yte >= query."""
        ret = blended_return(vanguard_gp, -3)
        # Smallest step with yte >= -3 is the 0-step (14.0/34.3/51.7)
        expected = 0.140 * 0.10 + 0.343 * 0.04 + 0.517 * 0.02
        assert ret == pytest.approx(expected)

    def test_beyond_max_step(self, vanguard_gp):
        """30 years out exceeds all steps, uses the highest (18)."""
        ret = blended_return(vanguard_gp, 30)
        expected = 0.95 * 0.10 + 0.05 * 0.04
        assert ret == pytest.approx(expected)

    def test_below_min_step(self, vanguard_gp):
        """Far post-enrollment uses the lowest step."""
        ret = blended_return(vanguard_gp, -10)
        expected = 0.116 * 0.10 + 0.284 * 0.04 + 0.600 * 0.02
        assert ret == pytest.approx(expected)


class TestGetReturnForYear:
    def test_flat_fallback(self):
        """When glide_path is None, returns resolve_nominal_return(assumptions)."""
        profile = CostProfile(label="T", current_total_cost=10_000, annual_cost_growth=0.0)
        child = Child(name="A", current_age=14, cost_profile=profile)
        assumptions = Assumptions(expected_return_nominal=0.07)
        ret = get_return_for_year(child, assumptions, 0)
        assert ret == pytest.approx(resolve_nominal_return(assumptions))

    def test_with_glide_path_varies_by_year(self, glide_child):
        """Return should differ between early and late years."""
        assumptions = Assumptions(expected_return_nominal=0.07)
        early = get_return_for_year(glide_child, assumptions, 0)  # 8 years out
        late = get_return_for_year(glide_child, assumptions, 7)  # 1 year out
        assert early > late

    def test_during_attendance(self, glide_child):
        """During attendance years, years_to_enrollment is 0."""
        assumptions = Assumptions(expected_return_nominal=0.07)
        # year_offset=8 is the first attendance year (start_age - current_age = 8)
        ret = get_return_for_year(glide_child, assumptions, 8)
        expected = blended_return(glide_child.glide_path, 0)
        assert ret == pytest.approx(expected)


class TestFactories:
    def test_vanguard_factory_valid(self):
        """Vanguard factory produces a valid glide path."""
        gp = vanguard_target_enrollment()
        assert len(gp.steps) > 0
        # All steps sum to ~1.0
        for step in gp.steps:
            assert step.equity_pct + step.bond_pct + step.short_term_pct == pytest.approx(1.0)

    def test_vanguard_factory_custom_returns(self):
        """Custom return overrides change the blended output."""
        gp_default = vanguard_target_enrollment()
        gp_custom = vanguard_target_enrollment(equity_return=0.12)
        # At 18 years (95% equity), custom should be higher
        ret_default = blended_return(gp_default, 18)
        ret_custom = blended_return(gp_custom, 18)
        assert ret_custom > ret_default

    def test_flat_equity_factory(self):
        """Flat equity produces 100% equity at all stages."""
        gp = flat_equity_glide_path(equity_return=0.10)
        for step in gp.steps:
            assert step.equity_pct == 1.0
            assert step.bond_pct == 0.0
            assert step.short_term_pct == 0.0
        # Return should be equity_return everywhere
        assert blended_return(gp, 18) == pytest.approx(0.10)
        assert blended_return(gp, 0) == pytest.approx(0.10)
