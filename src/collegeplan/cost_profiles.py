"""Factory functions for common school cost profiles.

Default costs are approximate 2025-2026 all-in COA figures
(tuition + room/board + fees + books) and are illustrative, not authoritative.
"""

from __future__ import annotations

from .models import CostProfile


def make_private_school_profile(
    current_total_cost: float = 65_000,
    annual_cost_growth: float = 0.05,
) -> CostProfile:
    return CostProfile(
        label="Private (4-year)",
        current_total_cost=current_total_cost,
        annual_cost_growth=annual_cost_growth,
    )


def make_public_instate_profile(
    current_total_cost: float = 28_000,
    annual_cost_growth: float = 0.04,
) -> CostProfile:
    return CostProfile(
        label="Public In-State (4-year)",
        current_total_cost=current_total_cost,
        annual_cost_growth=annual_cost_growth,
    )


def make_public_oos_profile(
    current_total_cost: float = 45_000,
    annual_cost_growth: float = 0.045,
) -> CostProfile:
    return CostProfile(
        label="Public Out-of-State (4-year)",
        current_total_cost=current_total_cost,
        annual_cost_growth=annual_cost_growth,
    )
