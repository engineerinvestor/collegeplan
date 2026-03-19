"""Shared-fund allocation policies for multi-child households."""

from __future__ import annotations

from .models import AllocationPolicy


def allocate_shared_withdrawal(
    policy: AllocationPolicy,
    available_balance: float,
    child_needs: dict[str, float],
    child_priority_order: list[str] | None = None,
) -> dict[str, float]:
    """Allocate shared pool funds to children for a single year.

    Args:
        policy: The allocation strategy to use.
        available_balance: Current shared pool balance available for withdrawal.
        child_needs: Mapping of child name to unfunded need for this year.
        child_priority_order: Names sorted oldest-first (lowest years_until_start).
            Required for OLDEST_FIRST policy.

    Returns:
        Mapping of child name to allocated amount from the shared pool.
    """
    # Filter to children that actually need funds this year
    active = {name: need for name, need in child_needs.items() if need > 0}
    if not active or available_balance <= 0:
        return {name: 0.0 for name in child_needs}

    total_need = sum(active.values())
    allocations: dict[str, float] = {name: 0.0 for name in child_needs}

    if policy == AllocationPolicy.EQUAL_SPLIT:
        per_child = available_balance / len(active)
        for name, need in active.items():
            allocations[name] = min(per_child, need)

    elif policy == AllocationPolicy.OLDEST_FIRST:
        if child_priority_order is None:
            # Fall back to dict order if not provided
            child_priority_order = list(active.keys())
        remaining = available_balance
        for name in child_priority_order:
            if name not in active:
                continue
            grant = min(remaining, active[name])
            allocations[name] = grant
            remaining -= grant
            if remaining <= 0:
                break

    elif policy == AllocationPolicy.PROPORTIONAL_TO_NEED:
        cap = min(available_balance, total_need)
        for name, need in active.items():
            allocations[name] = min(need, (need / total_need) * cap)

    return allocations
