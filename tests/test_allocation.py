"""Tests for shared-fund allocation policies."""

from collegeplan import AllocationPolicy
from collegeplan.allocation import allocate_shared_withdrawal


def test_equal_split_basic():
    needs = {"A": 1000, "B": 1000}
    result = allocate_shared_withdrawal(AllocationPolicy.EQUAL_SPLIT, 1000, needs)
    assert result["A"] == 500
    assert result["B"] == 500


def test_equal_split_capped_at_need():
    needs = {"A": 200, "B": 1000}
    result = allocate_shared_withdrawal(AllocationPolicy.EQUAL_SPLIT, 1000, needs)
    assert result["A"] == 200  # capped at need
    assert result["B"] == 500  # gets half of total available


def test_oldest_first():
    needs = {"A": 500, "B": 800}
    result = allocate_shared_withdrawal(
        AllocationPolicy.OLDEST_FIRST, 1000, needs, ["A", "B"]
    )
    assert result["A"] == 500
    assert result["B"] == 500  # remainder after A is fully funded


def test_proportional_to_need():
    needs = {"A": 300, "B": 700}
    result = allocate_shared_withdrawal(AllocationPolicy.PROPORTIONAL_TO_NEED, 500, needs)
    assert abs(result["A"] - 150) < 1e-10
    assert abs(result["B"] - 350) < 1e-10


def test_zero_need_gets_nothing():
    needs = {"A": 0, "B": 1000}
    result = allocate_shared_withdrawal(AllocationPolicy.EQUAL_SPLIT, 500, needs)
    assert result["A"] == 0.0
    assert result["B"] == 500
