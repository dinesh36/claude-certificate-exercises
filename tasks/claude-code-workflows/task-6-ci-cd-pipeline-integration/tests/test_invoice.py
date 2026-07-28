from billing.invoice import Invoice


def test_subtotal_sums_line_items():
    invoice = Invoice()
    invoice.add_line_item("Widget", 500, 3)
    invoice.add_line_item("Gadget", 1000, 1)
    assert invoice.subtotal_cents() == 2500


def test_empty_invoice_has_zero_subtotal():
    invoice = Invoice()
    assert invoice.subtotal_cents() == 0
