"""Tests for assumptions normalization (Fisher equation)."""


from collegeplan import Assumptions, deflate, normalize_assumptions
from collegeplan.assumptions import resolve_nominal_return, resolve_real_return


def test_nominal_to_real():
    a = Assumptions(expected_return_nominal=0.07, general_inflation=0.03)
    real = resolve_real_return(a)
    expected = (1.07 / 1.03) - 1
    assert abs(real - expected) < 1e-10


def test_real_to_nominal():
    a = Assumptions(expected_return_real=0.04, general_inflation=0.03)
    nominal = resolve_nominal_return(a)
    expected = (1.04 * 1.03) - 1
    assert abs(nominal - expected) < 1e-10


def test_normalize_populates_both():
    a = Assumptions(expected_return_nominal=0.07, general_inflation=0.03)
    n = normalize_assumptions(a)
    assert n.expected_return_nominal == 0.07
    assert n.expected_return_real is not None
    assert abs(n.expected_return_real - ((1.07 / 1.03) - 1)) < 1e-10


def test_deflate():
    assert abs(deflate(110.0, 1, 0.10) - 100.0) < 1e-10
    assert abs(deflate(100.0, 0, 0.05) - 100.0) < 1e-10
