"""Task 5: Batch Processing Strategies
Prompt Engineering & Structured Output
Sample vendor contracts for a weekly renewal-risk audit, plus the one urgent
contract reviewed synchronously instead.
"""

CONTRACTS = {
    "northwind": """\
NORTHWIND CLOUD HOSTING — MASTER SERVICES AGREEMENT (excerpt)

Term: This agreement renews automatically for successive 12-month terms
unless either party provides written notice of non-renewal at least 15 days
before the end of the then-current term.

Fees: Base hosting fee is $4,200/month, subject to change at renewal.
""",
    "meridian": """\
MERIDIAN OFFICE SUPPLIES — SUPPLY AGREEMENT (excerpt)

Term: This agreement runs for 12 months from the effective date. Either
party may terminate for convenience with 60 days' written notice. This
agreement does not renew automatically; a new agreement must be signed for
any subsequent term.

Fees: Pricing is fixed for the full term at the rates in Exhibit A.
""",
    "falcon": """\
FALCON LOGISTICS PARTNERS — FREIGHT SERVICES AGREEMENT (excerpt)

Term: 24-month initial term, renewing automatically thereafter.

Fees: Freight rates may be adjusted by Falcon at its sole discretion at any
time upon 10 days' notice, referencing "prevailing market conditions" with
no defined index or formula.
""",
    "brightpath": """\
BRIGHT PATH INSURANCE BROKERS — BROKERAGE AGREEMENT (excerpt)

Term: 12-month term. Renewal requires mutual written agreement at least 30
days before expiration; this agreement does not renew automatically.

Fees: Commission rates are fixed per the schedule in Exhibit B for the full
term.
""",
    "titan": "Titan Data Security amendment: +90 days.",
}

# Friday 6pm submission, Monday 9am deadline — comfortably more than the
# batch API's up-to-24-hour processing window, but the margin is what a real
# submission-timing decision has to check, not assume.
SUBMITTED_AT = "2026-08-07T18:00:00"
DEADLINE_AT = "2026-08-10T09:00:00"

# A contract under active negotiation, reviewed live on a call — this is the
# blocking counter-example to the weekly batch: the vendor is waiting on the
# phone right now, so there's no 24-hour window to spare.
URGENT_REVIEW_CONTRACT = """\
CASCADE ANALYTICS — DRAFT AMENDMENT (excerpt, under live negotiation)

Term: Renews automatically for successive 12-month terms unless either
party gives written notice of non-renewal at least 90 days before the end
of the then-current term.
"""
