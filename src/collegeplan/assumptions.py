"""Utility functions for normalizing return and inflation assumptions."""

from __future__ import annotations

from dataclasses import replace

from .models import Assumptions


def resolve_nominal_return(assumptions: Assumptions) -> float:
    """Return the nominal expected return, deriving from real if needed."""
    if assumptions.expected_return_nominal is not None:
        return assumptions.expected_return_nominal
    # Fisher equation: (1 + r_nom) = (1 + r_real)(1 + pi)
    r_real = assumptions.expected_return_real
    assert r_real is not None
    return (1 + r_real) * (1 + assumptions.general_inflation) - 1


def resolve_real_return(assumptions: Assumptions) -> float:
    """Return the real expected return, deriving from nominal if needed."""
    if assumptions.expected_return_real is not None:
        return assumptions.expected_return_real
    r_nom = assumptions.expected_return_nominal
    assert r_nom is not None
    return (1 + r_nom) / (1 + assumptions.general_inflation) - 1


def normalize_assumptions(assumptions: Assumptions) -> Assumptions:
    """Return a copy with both nominal and real returns populated."""
    return replace(
        assumptions,
        expected_return_nominal=resolve_nominal_return(assumptions),
        expected_return_real=resolve_real_return(assumptions),
    )


def deflate(nominal_value: float, years: int, inflation: float) -> float:
    """Convert a future nominal dollar amount to today's real dollars."""
    return nominal_value / (1 + inflation) ** years
