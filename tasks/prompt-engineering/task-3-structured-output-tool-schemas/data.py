"""Task 3: Structured Output Tool Schemas
Prompt Engineering & Structured Output
Sample accounting documents of unknown type, each shaped to exercise one or
more of the task statement's bullets (semantic mismatch, missing fields,
non-enum values, inconsistent date formats).
"""

INVOICE_MISMATCH = """\
ACME MACHINING LLC
123 Foundry Road, Toledo, OH

Invoice — Bill To: Riverside Fabricators
Date: March 14, 2024

Line Items:
  - CNC milling, batch #4471           $620.00
  - Replacement tooling                $410.00
  - Rush shipping surcharge            $210.00

Total Due: $1,300.00

Payment Terms: Net 30, plus a 2% early-payment discount if paid within 10 days.
Please remit payment in $ to the account on file.
"""

PURCHASE_ORDER_MISSING_DATE = """\
BOLT & NAIL HARDWARE SUPPLY
PURCHASE ORDER

PO Number: PO-55231
Date: 2024-03-20
Vendor: Timberline Lumber Co.

Line Items:
  - 2x4 lumber, 200 units               $840.00
  - Galvanized nails, 50 lb box         $95.00

Approval: Verbally approved by phone; written approval to follow.
"""

RECEIPT_CLEAN = """\
RIVERSIDE CAFE & CATERING
Receipt

Date: 14 Mar 2024

Line Items:
  - Catering platter (25 guests)        $312.50
  - Delivery fee                        $37.50

Total: $350.00

Paid via company card ending in 4471.
"""

SAMPLE_DOCUMENTS = {
    "invoice_mismatch": INVOICE_MISMATCH,
    "purchase_order_missing_date": PURCHASE_ORDER_MISSING_DATE,
    "receipt_clean": RECEIPT_CLEAN,
}
