"""Tests for exception classes."""

from collegeplan import CollegePlanError, SolverError, ValidationError


def test_validation_error_is_college_plan_error():
    assert issubclass(ValidationError, CollegePlanError)


def test_solver_error_is_college_plan_error():
    assert issubclass(SolverError, CollegePlanError)


def test_validation_error_message():
    exc = ValidationError("bad input")
    assert str(exc) == "bad input"


def test_solver_error_message():
    exc = SolverError("did not converge")
    assert str(exc) == "did not converge"


def test_college_plan_error_is_exception():
    assert issubclass(CollegePlanError, Exception)


def test_raise_and_catch_as_base():
    try:
        raise ValidationError("test")
    except CollegePlanError as exc:
        assert str(exc) == "test"


def test_solver_error_caught_as_base():
    try:
        raise SolverError("convergence failure")
    except CollegePlanError as exc:
        assert str(exc) == "convergence failure"
