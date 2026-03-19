"""Tests for the projection engine — the core simulation logic."""

from dataclasses import replace

import pytest

from collegeplan import (
    Assumptions,
    Child,
    ContributionTiming,
    CostProfile,
    HouseholdFund,
    project_child_plan,
    project_household_plan,
    vanguard_target_enrollment,
)


class TestSingleChildProjection:
    def test_zero_return_zero_growth_total_cost(self, simple_child, zero_return_assumptions):
        """With no growth and no return, total cost = years x current_cost."""
        result = project_child_plan(simple_child, zero_return_assumptions)
        assert result.projected_total_cost == pytest.approx(4 * 10_000)
        assert result.funded_amount == 0.0
        assert result.shortfall == pytest.approx(40_000)
        assert result.funded_ratio == 0.0

    def test_fully_prefunded(self, funded_child, zero_return_assumptions):
        """A child with enough balance covers everything, zero shortfall."""
        result = project_child_plan(funded_child, zero_return_assumptions)
        assert result.shortfall == pytest.approx(0.0)
        assert result.funded_ratio == pytest.approx(1.0)
        assert result.funded_amount == pytest.approx(40_000)

    def test_contributions_accumulate_zero_return(self, simple_child, zero_return_assumptions):
        """Contributions accumulate with no compounding noise at 0% return."""
        from dataclasses import replace

        child = replace(simple_child, annual_contribution=5_000)
        result = project_child_plan(child, zero_return_assumptions)
        # 8 years total (4 pre + 4 attendance), $5k/yr = $40k contributed
        # During pre-college: 4 years x $5k = $20k accumulated
        # During college: each year contributes $5k, and withdraws $10k
        # Year 4: begin=20000, +5k=25k, withdraw 10k → 15k
        # Year 5: begin=15000, +5k=20k, withdraw 10k → 10k
        # Year 6: begin=10000, +5k=15k, withdraw 10k → 5k
        # Year 7: begin=5000, +5k=10k, withdraw 10k → 0
        assert result.funded_ratio == pytest.approx(1.0)
        assert result.shortfall == pytest.approx(0.0)

    def test_withdrawal_capped_at_balance(self, zero_return_assumptions):
        """Balance never goes negative — withdrawal capped at available funds."""
        profile = CostProfile(label="Expensive", current_total_cost=100_000, annual_cost_growth=0.0)
        child = Child(
            name="C",
            current_age=17,
            cost_profile=profile,
            start_age=18,
            attendance_years=2,
            current_529_balance=50_000,
        )
        result = project_child_plan(child, zero_return_assumptions)
        # Cost = 200k, balance = 50k. Year 0 covers 50k of 100k, year 1 covers 0.
        for rec in result.schedule:
            assert rec.ending_balance >= 0.0
        assert result.funded_amount == pytest.approx(50_000)
        assert result.shortfall == pytest.approx(150_000)

    def test_boy_vs_eoy_timing(self, simple_child):
        """BOY timing grows contributions during the year they're made."""
        from dataclasses import replace

        child = replace(simple_child, annual_contribution=10_000, current_529_balance=0.0)
        a_nom = Assumptions(expected_return_nominal=0.10, general_inflation=0.0)
        a_boy = Assumptions(
            expected_return_nominal=0.10,
            general_inflation=0.0,
            contribution_timing=ContributionTiming.BEGINNING_OF_YEAR,
        )

        eoy = project_child_plan(child, a_nom)
        boy = project_child_plan(child, a_boy)

        # BOY should have a higher ending balance because contributions earn
        # return the year they're made (both fully fund here, so compare balances)
        boy_final = boy.schedule[-1].ending_balance
        eoy_final = eoy.schedule[-1].ending_balance
        assert boy_final > eoy_final

    def test_scholarship_pct_reduces_cost(self, simple_child, zero_return_assumptions):
        """scholarship_pct reduces each year's cost proportionally."""
        from dataclasses import replace

        child = replace(simple_child, scholarship_pct=0.5)
        result = project_child_plan(child, zero_return_assumptions)
        assert result.projected_total_cost == pytest.approx(4 * 5_000)

    def test_scholarship_offset_reduces_cost(self, simple_child, zero_return_assumptions):
        """scholarship_offset reduces cost by a fixed dollar amount."""
        from dataclasses import replace

        child = replace(simple_child, scholarship_offset=2_000)
        result = project_child_plan(child, zero_return_assumptions)
        assert result.projected_total_cost == pytest.approx(4 * 8_000)

    def test_years_until_start(self, simple_child, zero_return_assumptions):
        result = project_child_plan(simple_child, zero_return_assumptions)
        assert result.years_until_start == 4

    def test_first_year_cost(self, simple_child, zero_return_assumptions):
        result = project_child_plan(simple_child, zero_return_assumptions)
        assert result.projected_first_year_cost == pytest.approx(10_000)

    def test_glide_path_lower_funded_amount(self, nominal_assumptions):
        """A glide path produces a lower funded amount than a flat 7% return."""
        profile = CostProfile(label="T", current_total_cost=25_000, annual_cost_growth=0.04)
        child_flat = Child(
            name="Flat",
            current_age=10,
            cost_profile=profile,
            start_age=18,
            attendance_years=4,
            current_529_balance=30_000,
        )
        child_gp = replace(child_flat, name="GP", glide_path=vanguard_target_enrollment())

        result_flat = project_child_plan(child_flat, nominal_assumptions)
        result_gp = project_child_plan(child_gp, nominal_assumptions)

        assert result_gp.funded_amount < result_flat.funded_amount

    def test_glide_path_none_backward_compatible(self, simple_child, zero_return_assumptions):
        """Existing projections unchanged when glide_path is None."""
        result = project_child_plan(simple_child, zero_return_assumptions)
        assert result.projected_total_cost == pytest.approx(4 * 10_000)
        assert result.funded_amount == 0.0


class TestHouseholdProjection:
    def test_no_shared_fund_matches_individual(self, simple_child, zero_return_assumptions):
        """Household with no shared fund should match individual child projection."""
        individual = project_child_plan(simple_child, zero_return_assumptions)
        household = project_household_plan([simple_child], zero_return_assumptions)
        cr = household.child_results[0]
        assert cr.projected_total_cost == pytest.approx(individual.projected_total_cost)
        assert cr.funded_amount == pytest.approx(individual.funded_amount)
        assert cr.shortfall == pytest.approx(individual.shortfall)

    def test_shared_fund_covers_shortfall(self, simple_child, zero_return_assumptions):
        """A shared fund should cover per-child shortfalls."""
        hf = HouseholdFund(shared_balance=40_000)
        result = project_household_plan([simple_child], zero_return_assumptions, hf)
        cr = result.child_results[0]
        assert cr.funded_ratio == pytest.approx(1.0)
        assert cr.shortfall == pytest.approx(0.0)

    def test_overlap_years_detected(self, zero_return_assumptions):
        """Two children attending simultaneously produce overlap years."""
        profile = CostProfile(label="T", current_total_cost=10_000, annual_cost_growth=0.0)
        c1 = Child(name="A", current_age=16, cost_profile=profile, start_age=18, attendance_years=4)
        c2 = Child(name="B", current_age=15, cost_profile=profile, start_age=18, attendance_years=4)
        result = project_household_plan([c1, c2], zero_return_assumptions)
        # c1: years 2-5, c2: years 3-6 → overlap at years 3,4,5
        assert len(result.overlap_years) > 0

    def test_concurrent_enrollment_count(self, zero_return_assumptions):
        """concurrent_enrollment_by_year counts how many are enrolled each year."""
        profile = CostProfile(label="T", current_total_cost=10_000, annual_cost_growth=0.0)
        c1 = Child(name="A", current_age=17, cost_profile=profile, start_age=18, attendance_years=2)
        c2 = Child(name="B", current_age=17, cost_profile=profile, start_age=18, attendance_years=2)
        result = project_household_plan([c1, c2], zero_return_assumptions)
        # Both attend years 1-2
        for y in [1]:
            assert result.concurrent_enrollment_by_year.get(y, 0) == 2
