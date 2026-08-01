"""Sample listing documents and mock labeled data for NestList's listing-intake
pipeline (Domain 4 Steps 1/3/4, Domain 5 Step 5).

FEW_SHOT_* pairs are two worked examples in different source formats (a
structured MLS feed sheet, a narrative agent description) used as real
conversation-turn few-shot (Domain 4 Step 3). TEST_NARRATIVE_UNSEEN is a
third narrative listing, in neither worked example's property type, used to
check whether the model generalizes rather than pattern-matches the exact
cases it's seen.

BATCH_LISTINGS/VALIDATION_SET/TODAYS_QUEUE are documented further down.
"""

import random

# ---------------------------------------------------------------------------
# Few-shot examples (Domain 4 Steps 1 and 3)
# ---------------------------------------------------------------------------

FEW_SHOT_MLS_SHEET = """\
MLS LISTING SHEET
Listing ID: MLS-40021
Address: 812 Willow Creek Dr, Austin, TX
List Price: $475,000
Property Type: Single Family Detached
Year Built: 2004
Square Footage: 2,150 sq ft
Bedrooms: 4
Bathrooms: 2.5
HOA: None
"""

FEW_SHOT_MLS_EXTRACTION = {
    "listing_id": "MLS-40021",
    "address": "812 Willow Creek Dr, Austin, TX",
    "price": 475000,
    "property_type": "single_family",
    "property_type_other_detail": None,
    "square_footage": 2150,
    "year_built": 2004,
    "hoa_fee_monthly": None,
    "bedrooms": 4,
    "bathrooms": 2.5,
    "field_confidence": {
        "listing_id": 0.99, "address": 0.99, "price": 0.99, "property_type": 0.98,
        "square_footage": 0.97, "year_built": 0.98, "hoa_fee_monthly": 0.9,
        "bedrooms": 0.99, "bathrooms": 0.97,
    },
}

FEW_SHOT_NARRATIVE = """\
Charming 2-bed condo in the heart of Riverside! Unit 14C at 200 Harbor View Ln
is listed at $312,500. This well-maintained condo association charges
$260/month for building upkeep and amenities. Listing ref: MLS-40088.
"""

FEW_SHOT_NARRATIVE_EXTRACTION = {
    "listing_id": "MLS-40088",
    "address": "200 Harbor View Ln, Unit 14C",
    "price": 312500,
    "property_type": "condo",
    "property_type_other_detail": None,
    "square_footage": None,
    "year_built": None,
    "hoa_fee_monthly": 260,
    "bedrooms": 2,
    "bathrooms": None,
    "field_confidence": {
        "listing_id": 0.95, "address": 0.95, "price": 0.98, "property_type": 0.93,
        "square_footage": 0.0, "year_built": 0.0, "hoa_fee_monthly": 0.9,
        "bedrooms": 0.9, "bathrooms": 0.0,
    },
}

# Neither worked example above is an "other" property type, and neither is
# missing its price or address -- this one is, on both counts, to check
# generalization rather than pattern-matching the exact two cases seen.
TEST_NARRATIVE_UNSEEN = """\
Once-in-a-lifetime opportunity: a fully converted 19th-century lighthouse
keeper's cottage at 5 Beacon Point Rd, offered at $689,000. Listing
MLS-40199. This unique property has been lovingly restored, but the
seller's disclosure doesn't specify square footage or the exact year of
original construction. Two bedrooms.
"""

# ---------------------------------------------------------------------------
# Batch of listings for the weekly data-quality audit (Domain 4 Step 4)
# ---------------------------------------------------------------------------

# listing-40303 has exactly one numeric mention ("$199,000") -- no street
# number, no year, no sqft. _buggy_max_tokens_for (main.py) reserves 150
# tokens per numeric mention minus one, assuming every listing has at least
# two; this one hits (1 - 1) * 150 = 0, an invalid max_tokens value the API
# genuinely rejects. Not a staged failure -- a real per-document sizing bug
# that happens to reproduce on whichever listing is terse enough.
BATCH_LISTINGS = {
    "listing-40301": "812 Willow Creek Dr, Austin, TX. Listed at $475,000. Single family, 4 bed, 2.5 bath, built 2004, 2150 sqft. No HOA.",
    "listing-40302": "200 Harbor View Ln Unit 14C. Condo listed at $312,500. HOA $260/month. 2 bedrooms.",
    "listing-40303": "Lighthouse Point Way. Listed at $199,000.",
    "listing-40304": "44 Birchwood Ct, listed at $528,900. Townhouse, 3 bed, 2 bath, built 1998, 1780 sqft.",
    "listing-40305": "9 Cedar Hollow Rd, listed at $612,000. Multi-family duplex, built 1965, 2400 sqft, 4 bedrooms total.",
    "listing-40306": "77 Prairie View Ave, listed at $355,000. Condo, 1 bed, 1 bath, HOA $180/month.",
}

# Submitted Friday evening for a Monday-morning weekly data-quality review --
# comfortably more than the batch API's up-to-24-hour processing window, the
# margin worked out in main.py rather than assumed.
BATCH_SUBMITTED_AT = "2026-08-07T20:00:00"
BATCH_DEADLINE_AT = "2026-08-10T06:00:00"

# ---------------------------------------------------------------------------
# Labeled validation set and today's queue for confidence-routing (Domain 5 Step 5)
# ---------------------------------------------------------------------------

FIELDS = ["price", "property_type", "square_footage", "year_built", "hoa_fee_monthly", "bedrooms", "bathrooms"]

# Ground-truth extraction accuracy per (source, field) segment. Every
# segment is high except narrative/square_footage, which is the hidden
# problem an aggregate accuracy number would mask: narrative agent
# descriptions almost never state an exact interior square footage the way
# an MLS sheet does, so the model is guessing far more often than its
# confidence scores would suggest.
SEGMENT_ACCURACY = {
    ("mls_feed", "price"): 0.99,
    ("mls_feed", "property_type"): 0.98,
    ("mls_feed", "square_footage"): 0.97,
    ("mls_feed", "year_built"): 0.98,
    ("mls_feed", "hoa_fee_monthly"): 0.96,
    ("mls_feed", "bedrooms"): 0.99,
    ("mls_feed", "bathrooms"): 0.97,
    ("narrative", "price"): 0.95,
    ("narrative", "property_type"): 0.93,
    ("narrative", "square_footage"): 0.52,
    ("narrative", "year_built"): 0.90,
    ("narrative", "hoa_fee_monthly"): 0.91,
    ("narrative", "bedrooms"): 0.94,
    ("narrative", "bathrooms"): 0.92,
}

DOCUMENT_COUNTS = {"mls_feed": 24, "narrative": 16}


def _confidence_for(source, field, is_correct, rng):
    """The model stays confident on narrative/square_footage regardless of
    whether it's actually right -- narrative descriptions often use a vague
    phrase ("plenty of room downstairs") near a number that isn't actually
    the square footage, and the model latches onto it anyway."""
    if (source, field) == ("narrative", "square_footage"):
        return round(rng.uniform(0.82, 0.96), 2)
    if is_correct:
        return round(rng.uniform(0.90, 0.99), 2)
    return round(rng.uniform(0.55, 0.85), 2)


def _build_validation_set(seed=42):
    """Assign correctness deterministically per segment (round(accuracy * N)
    correct, rest incorrect, order shuffled) rather than an independent coin
    flip per record -- with only 16-24 documents per source, a coin flip's
    sampling noise would blur out the deliberate per-segment rates this
    fixture depends on."""
    rng = random.Random(seed)
    doc_ids_by_source = {}
    doc_id = 0
    for source, count in DOCUMENT_COUNTS.items():
        ids = []
        for _ in range(count):
            doc_id += 1
            ids.append(f"LST-{doc_id:04d}")
        doc_ids_by_source[source] = ids

    records = []
    for source, ids in doc_ids_by_source.items():
        for field in FIELDS:
            accuracy = SEGMENT_ACCURACY[(source, field)]
            n = len(ids)
            n_correct = round(accuracy * n)
            correctness = [True] * n_correct + [False] * (n - n_correct)
            rng.shuffle(correctness)
            for document_id, is_correct in zip(ids, correctness):
                records.append({
                    "document_id": document_id,
                    "source": source,
                    "field": field,
                    "model_confidence": _confidence_for(source, field, is_correct, rng),
                    "is_correct": is_correct,
                })
    return records


VALIDATION_SET = _build_validation_set()

# Today's incoming extraction queue, waiting to be routed to auto-approve or
# human review. Mixes: comfortably high-confidence items, the known-bad
# segment (narrative/square_footage) shown at high confidence anyway,
# genuinely low-confidence items, and one flagged ambiguous_source (the
# underlying document itself was hard to read, independent of confidence).
TODAYS_QUEUE = [
    {"document_id": "LST-Q001", "source": "mls_feed", "field": "price", "model_confidence": 0.98, "ambiguous_source": False},
    {"document_id": "LST-Q002", "source": "mls_feed", "field": "square_footage", "model_confidence": 0.97, "ambiguous_source": False},
    {"document_id": "LST-Q003", "source": "narrative", "field": "square_footage", "model_confidence": 0.90, "ambiguous_source": False},
    {"document_id": "LST-Q004", "source": "narrative", "field": "square_footage", "model_confidence": 0.88, "ambiguous_source": False},
    {"document_id": "LST-Q005", "source": "narrative", "field": "property_type", "model_confidence": 0.71, "ambiguous_source": False},
    {"document_id": "LST-Q006", "source": "mls_feed", "field": "hoa_fee_monthly", "model_confidence": 0.65, "ambiguous_source": True},
    {"document_id": "LST-Q007", "source": "narrative", "field": "price", "model_confidence": 0.93, "ambiguous_source": False},
    {"document_id": "LST-Q008", "source": "mls_feed", "field": "year_built", "model_confidence": 0.99, "ambiguous_source": False},
    {"document_id": "LST-Q009", "source": "narrative", "field": "bathrooms", "model_confidence": 0.60, "ambiguous_source": False},
    {"document_id": "LST-Q010", "source": "narrative", "field": "hoa_fee_monthly", "model_confidence": 0.89, "ambiguous_source": False},
]

# Real listing excerpt for the live claude -p confidence call -- deliberately
# the same problem segment (narrative/square_footage) the mock data flags.
SAMPLE_NARRATIVE_FOR_LIVE_CHECK = """\
Sun-drenched 3-bedroom retreat at 18 Sparrow Hollow Ln, listed at $441,000.
Vaulted ceilings and an open-concept layout make the main level feel much
bigger than a typical starter home -- plenty of room for a growing family.
Built in the late 1990s. No HOA.
"""
