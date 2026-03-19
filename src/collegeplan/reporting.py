"""Serialization helpers for projection results."""

from __future__ import annotations

import dataclasses
import enum
import json
from typing import Any

# Fields that represent rates, ratios, or ages — NOT dollar amounts.
_NO_ROUND_FIELDS = frozenset(
    {
        "funded_ratio",
        "achieved_funding_ratio",
        "scholarship_pct",
        "annual_cost_growth",
        "general_inflation",
        "expected_return_nominal",
        "expected_return_real",
        "child_age",
        "target_funding_ratio",
        "contribution_growth_rate",
    }
)


def _clean(obj: Any, field_name: str = "") -> Any:
    """Recursively convert a dataclass-derived structure for JSON output."""
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {f.name: _clean(getattr(obj, f.name), f.name) for f in dataclasses.fields(obj)}
    if isinstance(obj, enum.Enum):
        return obj.value
    if isinstance(obj, dict):
        return {k: _clean(v, k if isinstance(k, str) else "") for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(item, field_name) for item in obj]
    if isinstance(obj, float):
        if field_name in _NO_ROUND_FIELDS:
            return obj
        return round(obj)
    return obj


def to_dict(result: Any) -> dict[str, Any]:
    """Convert a result dataclass to a JSON-compatible dict.

    Dollar amounts are rounded to the nearest integer.
    Enum values become their string values.
    Tuples become lists.
    """
    out: dict[str, Any] = _clean(result)
    return out


def to_dataframe(result: Any) -> Any:
    """Convert a projection result to a pandas DataFrame.

    Accepts ``ChildProjectionResult``, ``HouseholdProjectionResult``,
    or ``SensitivityResult``. Full float precision is preserved (no rounding).

    Raises ``ImportError`` with a helpful message when pandas is not installed.
    """
    try:
        import pandas as pd  # type: ignore[import-untyped,unused-ignore]
    except ImportError:
        raise ImportError(
            "pandas is required for to_dataframe(). "
            "Install it with: pip install 'collegeplan[pandas]'"
        ) from None

    if dataclasses.is_dataclass(result) and not isinstance(result, type):
        fields = {f.name for f in dataclasses.fields(result)}
    else:
        fields = set()

    if "schedule" in fields and "child_name" in fields and "child_results" not in fields:
        # ChildProjectionResult
        rows = [dataclasses.asdict(rec) for rec in result.schedule]
        return pd.DataFrame(rows)

    if "child_results" in fields and "schedule" in fields:
        # HouseholdProjectionResult
        frames: list[Any] = []
        for cr in result.child_results:
            df = pd.DataFrame([dataclasses.asdict(rec) for rec in cr.schedule])
            df["child_name"] = cr.child_name
            frames.append(df)
        shared_df = pd.DataFrame([dataclasses.asdict(rec) for rec in result.schedule])
        shared_df["child_name"] = "shared_fund"
        frames.append(shared_df)
        return pd.concat(frames, ignore_index=True)

    if "scenarios" in fields:
        # SensitivityResult
        rows_list: list[dict[str, Any]] = []
        for case in result.scenarios:
            row: dict[str, Any] = dict(case.parameters)
            if case.savings_solution is not None:
                row["required_annual_contribution"] = (
                    case.savings_solution.required_annual_contribution
                )
                row["required_monthly_contribution"] = (
                    case.savings_solution.required_monthly_contribution
                )
                row["achieved_funding_ratio"] = case.savings_solution.achieved_funding_ratio
            rows_list.append(row)
        return pd.DataFrame(rows_list)

    raise TypeError(
        f"Unsupported result type: {type(result).__name__}. "
        "Expected ChildProjectionResult, HouseholdProjectionResult, or SensitivityResult."
    )


def to_json(result: Any, **kwargs: Any) -> str:
    """Serialize a result dataclass to a JSON string.

    Accepts any keyword arguments supported by ``json.dumps``.
    Defaults to ``indent=2`` if not specified.
    """
    kwargs.setdefault("indent", 2)
    return json.dumps(to_dict(result), **kwargs)
