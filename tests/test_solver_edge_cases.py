"""Edge-case tests for the solver: convergence, extremes, and weighted suggestions."""

from dataclasses import replace

import pytest

from collegeplan import (
    Assumptions,
    Child,
    CostProfile,
    SolverError,
    project_household_plan,
    solve_required_savings,
)


@pytest.fixture
def expensive_child():
    profile = CostProfile(label="Expensive", current_total_cost=80_000, annual_cost_growth=0.06)
    return Child(
        name="Expensive",
        current_age=15,
        cost_profile=profile,
        start_age=18,
        attendance_years=4,
    )


@pytest.fixture
def cheap_child():
    profile = CostProfile(label="Cheap", current_total_cost=20_000, annual_cost_growth=0.03)
    return Child(
        name="Cheap",
        current_age=5,
        cost_profile=profile,
        start_age=18,
        attendance_years=4,
    )


@pytest.fixture
def basic_assumptions():
    return Assumptions(expected_return_nominal=0.07, general_inflation=0.03)


class TestSolverConvergence:
    def test_max_iterations_one_raises(self, expensive_child, basic_assumptions):
        """A single iteration cannot converge for a meaningful problem."""
        with pytest.raises(SolverError, match="did not converge"):
            solve_required_savings(
                [expensive_child],
                basic_assumptions,
                max_iterations=1,
            )

    def test_tight_tolerance(self, expensive_child, basic_assumptions):
        """Solver converges even with very tight tolerance."""
        sol = solve_required_savings(
            [expensive_child],
            basic_assumptions,
            tolerance=0.01,
        )
        assert sol.required_annual_contribution > 0
        assert sol.achieved_funding_ratio >= 0.999

    def test_already_overfunded(self, basic_assumptions):
        """Child with huge balance needs zero additional savings."""
        profile = CostProfile(label="T", current_total_cost=10_000, annual_cost_growth=0.0)
        child = Child(
            name="Rich",
            current_age=16,
            cost_profile=profile,
            start_age=18,
            attendance_years=4,
            current_529_balance=1_000_000,
        )
        sol = solve_required_savings([child], basic_assumptions)
        assert sol.required_annual_contribution == 0.0
        # Withdrawal capping means ratio is exactly 1.0, not above
        assert sol.achieved_funding_ratio >= 1.0


class TestExtremeTargets:
    def test_very_low_target(self, expensive_child, basic_assumptions):
        """Solving for 10% funding should require less than full funding."""
        sol_low = solve_required_savings(
            [expensive_child], basic_assumptions, target_funding_ratio=0.10
        )
        sol_full = solve_required_savings(
            [expensive_child], basic_assumptions, target_funding_ratio=1.0
        )
        assert sol_low.required_annual_contribution < sol_full.required_annual_contribution

    def test_high_target_still_fully_funded(self, expensive_child, basic_assumptions):
        """Solving for 99% funding achieves at least that ratio."""
        sol = solve_required_savings(
            [expensive_child], basic_assumptions, target_funding_ratio=0.99
        )
        assert sol.achieved_funding_ratio >= 0.98


class TestUpperBoundDoubling:
    def test_child_about_to_start(self, basic_assumptions):
        """Child starting next year needs a high contribution; upper bound doubles."""
        profile = CostProfile(label="T", current_total_cost=50_000, annual_cost_growth=0.04)
        child = Child(
            name="Senior",
            current_age=17,
            cost_profile=profile,
            start_age=18,
            attendance_years=4,
        )
        sol = solve_required_savings([child], basic_assumptions)
        assert sol.required_annual_contribution > 0
        assert sol.achieved_funding_ratio >= 0.999


class TestWeightedSuggestions:
    def test_suggestions_sum_to_total(self, expensive_child, cheap_child, basic_assumptions):
        """Per-child suggestions should sum to the total annual contribution."""
        sol = solve_required_savings(
            [expensive_child, cheap_child],
            basic_assumptions,
        )
        total_suggestions = sum(sol.per_child_suggestions.values())
        assert total_suggestions == pytest.approx(sol.required_annual_contribution, rel=1e-6)

    def test_expensive_child_gets_more(self, expensive_child, cheap_child, basic_assumptions):
        """Child with higher projected cost gets a larger suggestion."""
        sol = solve_required_savings(
            [expensive_child, cheap_child],
            basic_assumptions,
        )
        assert sol.per_child_suggestions["Expensive"] > sol.per_child_suggestions["Cheap"]

    def test_weighted_suggestions_close_the_loop(
        self, expensive_child, cheap_child, basic_assumptions
    ):
        """Feeding weighted suggestions back achieves the target funding ratio."""
        sol = solve_required_savings(
            [expensive_child, cheap_child],
            basic_assumptions,
        )
        modified = [
            replace(
                c,
                annual_contribution=c.annual_contribution + sol.per_child_suggestions[c.name],
            )
            for c in [expensive_child, cheap_child]
        ]
        result = project_household_plan(modified, basic_assumptions)
        total_funded = sum(cr.funded_amount for cr in result.child_results)
        total_cost = result.total_projected_spend
        ratio = total_funded / total_cost
        assert ratio >= 0.999, f"Funding ratio {ratio} is below 0.999"

    def test_single_child_weight_is_full(self, expensive_child, basic_assumptions):
        """Single child gets 100% of the suggestion."""
        sol = solve_required_savings([expensive_child], basic_assumptions)
        assert sol.per_child_suggestions["Expensive"] == pytest.approx(
            sol.required_annual_contribution
        )

    def test_shared_pool_suggestions_equal(self, expensive_child, cheap_child, basic_assumptions):
        """In shared_pool mode, per_child_suggestions split equally."""
        sol = solve_required_savings(
            [expensive_child, cheap_child],
            basic_assumptions,
            solve_mode="shared_pool",
        )
        n = 2
        for _name, amount in sol.per_child_suggestions.items():
            assert amount == pytest.approx(sol.required_annual_contribution / n)
