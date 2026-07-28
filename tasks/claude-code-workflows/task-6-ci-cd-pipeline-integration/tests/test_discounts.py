import pytest

from billing.discounts import apply_percentage_discount


def test_no_discount():
    assert apply_percentage_discount(1000, 0) == 1000


def test_partial_discount():
    assert apply_percentage_discount(1000, 25) == 750


def test_full_discount():
    assert apply_percentage_discount(1000, 100) == 0


def test_rejects_out_of_range():
    with pytest.raises(ValueError):
        apply_percentage_discount(1000, 150)
