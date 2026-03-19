"""collegeplan — deterministic college cost projection and savings planning engine."""

from .allocation import allocate_shared_withdrawal as allocate_shared_withdrawal
from .assumptions import deflate as deflate
from .assumptions import normalize_assumptions as normalize_assumptions
from .cost_profiles import make_private_school_profile as make_private_school_profile
from .cost_profiles import make_public_instate_profile as make_public_instate_profile
from .cost_profiles import make_public_oos_profile as make_public_oos_profile
from .engine import project_child_plan as project_child_plan
from .engine import project_household_plan as project_household_plan
from .exceptions import CollegePlanError as CollegePlanError
from .exceptions import SolverError as SolverError
from .exceptions import ValidationError as ValidationError
from .models import AllocationPolicy as AllocationPolicy
from .models import Assumptions as Assumptions
from .models import Child as Child
from .models import ChildProjectionResult as ChildProjectionResult
from .models import ContributionTiming as ContributionTiming
from .models import CostProfile as CostProfile
from .models import HouseholdFund as HouseholdFund
from .models import HouseholdProjectionResult as HouseholdProjectionResult
from .models import SavingsSolution as SavingsSolution
from .models import SensitivityCase as SensitivityCase
from .models import SensitivityResult as SensitivityResult
from .models import YearRecord as YearRecord
from .reporting import to_dict as to_dict
from .reporting import to_json as to_json
from .sensitivity import run_sensitivity as run_sensitivity
from .solver import solve_required_savings as solve_required_savings

__all__ = [
    "AllocationPolicy",
    "Assumptions",
    "Child",
    "ChildProjectionResult",
    "CollegePlanError",
    "ContributionTiming",
    "CostProfile",
    "HouseholdFund",
    "HouseholdProjectionResult",
    "SavingsSolution",
    "SensitivityCase",
    "SensitivityResult",
    "SolverError",
    "ValidationError",
    "YearRecord",
    "allocate_shared_withdrawal",
    "deflate",
    "make_private_school_profile",
    "make_public_instate_profile",
    "make_public_oos_profile",
    "normalize_assumptions",
    "project_child_plan",
    "project_household_plan",
    "run_sensitivity",
    "solve_required_savings",
    "to_dict",
    "to_json",
]
