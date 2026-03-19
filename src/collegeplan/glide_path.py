"""Glide path asset allocation for age-based 529 investment strategies."""

from __future__ import annotations

from .assumptions import resolve_nominal_return
from .models import Assumptions, Child, GlidePath, GlidePathStep


def blended_return(glide_path: GlidePath, years_to_enrollment: int) -> float:
    """Compute the weighted-average nominal return for a given years-to-enrollment.

    Finds the step with the smallest ``years_to_enrollment`` that is >= the
    query value. If the query exceeds all steps, the highest step is used.
    If below all steps, the lowest step is used.
    """
    # Steps are sorted descending by years_to_enrollment.
    # Find the step with the smallest yte >= query. If none qualifies,
    # use the highest step (first). If query is below all, use the lowest (last).
    step = glide_path.steps[0]  # default: highest step (beyond max)
    for s in glide_path.steps:
        if s.years_to_enrollment >= years_to_enrollment:
            step = s  # candidate; keep scanning for a tighter (smaller) match
        else:
            break

    return (
        step.equity_pct * glide_path.equity_return
        + step.bond_pct * glide_path.bond_return
        + step.short_term_pct * glide_path.short_term_return
    )


def get_return_for_year(child: Child, assumptions: Assumptions, year_offset: int) -> float:
    """Return the nominal expected return for a child at a given year offset.

    If the child has no glide path, falls back to the flat rate from
    ``assumptions``. Otherwise, computes ``years_to_enrollment`` and looks
    up the blended return from the glide path schedule.
    """
    if child.glide_path is None:
        return resolve_nominal_return(assumptions)

    years_to_enrollment = max(0, int(child.start_age - child.current_age) - year_offset)
    return blended_return(child.glide_path, years_to_enrollment)


# ---------------------------------------------------------------------------
# Factory presets
# ---------------------------------------------------------------------------


def vanguard_target_enrollment(
    equity_return: float = 0.10,
    bond_return: float = 0.04,
    short_term_return: float = 0.02,
) -> GlidePath:
    """Vanguard target enrollment glide path based on published allocations."""
    S = GlidePathStep
    steps = (
        S(years_to_enrollment=18, equity_pct=0.950, bond_pct=0.050, short_term_pct=0.000),
        S(years_to_enrollment=15, equity_pct=0.880, bond_pct=0.120, short_term_pct=0.000),
        S(years_to_enrollment=13, equity_pct=0.785, bond_pct=0.215, short_term_pct=0.000),
        S(years_to_enrollment=11, equity_pct=0.665, bond_pct=0.335, short_term_pct=0.000),
        S(years_to_enrollment=9, equity_pct=0.560, bond_pct=0.440, short_term_pct=0.000),
        S(years_to_enrollment=7, equity_pct=0.480, bond_pct=0.520, short_term_pct=0.000),
        S(years_to_enrollment=5, equity_pct=0.323, bond_pct=0.560, short_term_pct=0.117),
        S(years_to_enrollment=3, equity_pct=0.224, bond_pct=0.526, short_term_pct=0.250),
        S(years_to_enrollment=1, equity_pct=0.179, bond_pct=0.438, short_term_pct=0.383),
        S(years_to_enrollment=0, equity_pct=0.140, bond_pct=0.343, short_term_pct=0.517),
        S(years_to_enrollment=-4, equity_pct=0.116, bond_pct=0.284, short_term_pct=0.600),
    )
    return GlidePath(
        steps=steps,
        equity_return=equity_return,
        bond_return=bond_return,
        short_term_return=short_term_return,
    )


def flat_equity_glide_path(equity_return: float = 0.10) -> GlidePath:
    """100% equity at all stages, for comparison against age-based strategies."""
    steps = (
        GlidePathStep(years_to_enrollment=18, equity_pct=1.0, bond_pct=0.0, short_term_pct=0.0),
        GlidePathStep(years_to_enrollment=0, equity_pct=1.0, bond_pct=0.0, short_term_pct=0.0),
        GlidePathStep(years_to_enrollment=-4, equity_pct=1.0, bond_pct=0.0, short_term_pct=0.0),
    )
    return GlidePath(
        steps=steps,
        equity_return=equity_return,
        bond_return=0.0,
        short_term_return=0.0,
    )
