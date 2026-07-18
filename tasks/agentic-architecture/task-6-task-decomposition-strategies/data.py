"""Mock manufacturing quality-control data for the task (Domain 1.6).

BATCHES backs the fixed pipeline (inspect_batch + the cross-batch trend
pass) — two of the three batches share the evening shift and both run high
defect counts, giving the trend pass a real pattern to surface.

DEFECT_REPORTS backs the dynamic path: scope_customer_defect_report decides
which of ROOT_CAUSE_AREAS actually get flagged for a given product, and only
those get a follow-up investigate_root_cause call. PRODUCT-A flags a single
area, PRODUCT-B flags two — the fan-out genuinely varies per product rather
than following a fixed script.
"""

BATCHES = {
    "BATCH-101": {"shift": "morning", "defect_count": 2, "dimensional_tolerance_ok": True, "surface_finish_ok": True},
    "BATCH-102": {"shift": "evening", "defect_count": 14, "dimensional_tolerance_ok": False, "surface_finish_ok": True},
    "BATCH-103": {"shift": "evening", "defect_count": 11, "dimensional_tolerance_ok": False, "surface_finish_ok": True},
}

# Every root-cause area a scope could possibly flag. Only the ones present
# in a product's DEFECT_REPORTS entry below actually come back flagged; the
# rest report clean when scoped.
ROOT_CAUSE_AREAS = ["materials", "calibration", "process_step", "packaging"]

DEFECT_REPORTS = {
    "PRODUCT-A": {
        "reported_issue": "Cracking near the left edge on a batch of returned units.",
        "flagged_areas": {
            "materials": "Raw material lot #M-2291 tested below spec tensile strength for this run.",
        },
    },
    "PRODUCT-B": {
        "reported_issue": "Inconsistent wall thickness reported by a customer.",
        "flagged_areas": {
            "calibration": "Extrusion die sensor drifted 0.4mm out of calibration mid-shift.",
            "process_step": "Cooling stage residence time was reduced during a line-speed change.",
        },
    },
}
