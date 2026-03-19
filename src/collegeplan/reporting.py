"""Serialization helpers for projection results."""

from __future__ import annotations

import dataclasses
import enum
import json
from typing import Any

# Fields that represent rates, ratios, or ages — NOT dollar amounts.
_NO_ROUND_FIELDS = frozenset({
    "funded_ratio",
    "achieved_funding_ratio",
    "scholarship_pct",
    "annual_cost_growth",
    "general_inflation",
    "expected_return_nominal",
    "expected_return_real",
    "child_age",
    "target_funding_ratio",
})


def _clean(obj: Any, field_name: str = "") -> Any:
    """Recursively convert a dataclass-derived structure for JSON output."""
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {
            f.name: _clean(getattr(obj, f.name), f.name)
            for f in dataclasses.fields(obj)
        }
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


def to_json(result: Any, **kwargs: Any) -> str:
    """Serialize a result dataclass to a JSON string.

    Accepts any keyword arguments supported by ``json.dumps``.
    Defaults to ``indent=2`` if not specified.
    """
    kwargs.setdefault("indent", 2)
    return json.dumps(to_dict(result), **kwargs)
