"""Custom exceptions for the collegeplan package."""


class CollegePlanError(Exception):
    """Base exception for all collegeplan errors."""


class ValidationError(CollegePlanError):
    """Raised when input validation fails."""


class SolverError(CollegePlanError):
    """Raised when the savings solver fails to converge."""
