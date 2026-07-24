"""Tests for reports.py's legacy_order_total."""

from reports import legacy_order_total


def test_legacy_order_total_sums_line_items():
    assert legacy_order_total([("WIDGET-1", 10.0, 2), ("WIDGET-2", 5.0, 1)]) == 25.0
