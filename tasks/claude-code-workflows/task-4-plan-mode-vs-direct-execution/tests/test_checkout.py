"""Tests for the checkout flow: cart, discounts, payment, inventory, and orchestration."""

import pytest

from cart import Cart
from discounts import apply_discount, validate_code
from inventory import _STOCK, OutOfStockError, reserve_stock
from order_service import checkout
from payment_processor import PaymentDeclinedError, charge


def test_add_item_increases_subtotal():
    cart = Cart()
    cart.add_item("WIDGET-1", 10.0, 2)
    assert cart.subtotal() == 20.0


def test_remove_item_removes_it():
    cart = Cart()
    cart.add_item("WIDGET-1", 10.0, 1)
    cart.remove_item("WIDGET-1")
    assert cart.subtotal() == 0.0


def test_validate_code_accepts_known_code():
    assert validate_code("SAVE10") is True


def test_validate_code_rejects_unknown_code():
    assert validate_code("NOPE") is False


def test_apply_discount_reduces_subtotal():
    assert apply_discount(100.0, "SAVE10") == 90.0


def test_apply_discount_ignores_invalid_code():
    assert apply_discount(100.0, "NOPE") == 100.0


def test_charge_returns_transaction_id():
    txn = charge(50.0, "tok_good")
    assert txn.startswith("txn_tok_good_")


def test_charge_declines_bad_card():
    with pytest.raises(PaymentDeclinedError):
        charge(50.0, "declined")


def test_charge_rejects_non_positive_amount():
    with pytest.raises(ValueError):
        charge(0, "tok_good")


def test_reserve_stock_deducts_quantity():
    before = _STOCK["WIDGET-1"]
    reserve_stock("WIDGET-1", 1)
    assert _STOCK["WIDGET-1"] == before - 1


def test_reserve_stock_raises_when_insufficient():
    with pytest.raises(OutOfStockError):
        reserve_stock("WIDGET-2", 999)


def test_checkout_runs_full_flow():
    cart = Cart()
    cart.add_item("WIDGET-1", 10.0, 1)
    result = checkout(cart, "tok_good", "buyer@example.com")
    assert result["total"] == 10.0
    assert result["transaction_id"].startswith("txn_")


def test_checkout_applies_discount_code():
    cart = Cart()
    cart.add_item("WIDGET-1", 100.0, 1)
    result = checkout(cart, "tok_good", "buyer@example.com", discount_code="SAVE10")
    assert result["total"] == 90.0
