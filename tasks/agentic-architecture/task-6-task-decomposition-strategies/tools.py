"""Tool schemas and implementations for the quality-control coordinator (Domain 1.6).

_inspect_batch / _run_cross_batch_defect_trend are the fixed pipeline (Task
Statement 1.6's prompt-chaining pattern): every named batch gets the same
predictable inspection, then one integration pass looks for a cross-batch
trend. _scope_customer_defect_report / _investigate_root_cause are the
dynamic path: the scope decides which root-cause areas actually warrant a
deeper _investigate_root_cause call — a different subset per product, not a
fixed script.

The only export is TOOLS: a list of {"schema": ..., "implementation": ...}
entries. common/agent_loop.py extracts the schemas for the Anthropic API
call and builds its own name -> implementation map to dispatch tool_use
blocks directly — nothing else in this module needs to be imported
elsewhere.
"""

from common.errors import tool_error

from data import BATCHES, DEFECT_REPORTS, ROOT_CAUSE_AREAS

# ---------------------------------------------------------------------------
# Tool implementations — fixed pipeline
# ---------------------------------------------------------------------------

def _inspect_batch(batch_id: str) -> dict:
    batch = BATCHES.get(batch_id)
    if batch is None:
        return tool_error("validation", False, f"No batch found with ID '{batch_id}'.")
    return {"batch_id": batch_id, **batch}


def _run_cross_batch_defect_trend(findings: list[dict]) -> dict:
    if not findings:
        return tool_error(
            "validation",
            False,
            "findings must contain at least one prior inspect_batch result to analyze.",
        )

    by_shift: dict[str, list[int]] = {}
    for f in findings:
        by_shift.setdefault(f["shift"], []).append(f["defect_count"])
    shift_averages = {shift: sum(counts) / len(counts) for shift, counts in by_shift.items()}

    worst_shift = max(shift_averages, key=shift_averages.get) if len(shift_averages) > 1 else None
    concentrated = worst_shift is not None and shift_averages[worst_shift] > 2 * min(shift_averages.values())

    return {
        "batches_analyzed": [f["batch_id"] for f in findings],
        "shift_averages": shift_averages,
        "trend": (
            f"Defect counts are concentrated in the {worst_shift} shift."
            if concentrated
            else "No strong cross-batch pattern found."
        ),
    }


# ---------------------------------------------------------------------------
# Tool implementations — dynamic path
# ---------------------------------------------------------------------------

def _scope_customer_defect_report(product_id: str) -> dict:
    report = DEFECT_REPORTS.get(product_id)
    if report is None:
        return tool_error("validation", False, f"No defect report found for product '{product_id}'.")

    return {
        "product_id": product_id,
        "reported_issue": report["reported_issue"],
        "areas_checked": ROOT_CAUSE_AREAS,
        "areas_flagged": list(report["flagged_areas"]),
    }


def _investigate_root_cause(product_id: str, area: str) -> dict:
    report = DEFECT_REPORTS.get(product_id)
    if report is None:
        return tool_error("validation", False, f"No defect report found for product '{product_id}'.")
    if area not in ROOT_CAUSE_AREAS:
        return tool_error(
            "validation", False, f"Unknown area '{area}'. Valid areas: {', '.join(ROOT_CAUSE_AREAS)}."
        )
    if area not in report["flagged_areas"]:
        return tool_error(
            "validation",
            False,
            f"'{area}' was not flagged by scope_customer_defect_report for '{product_id}' — nothing to investigate there.",
        )

    return {"product_id": product_id, "area": area, "finding": report["flagged_areas"][area]}


# ---------------------------------------------------------------------------
# TOOLS — the only export: one {schema, implementation} entry per tool
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "schema": {
            "name": "inspect_batch",
            "description": (
                "Run the standard quality inspection on ONE named production batch — defect "
                "count, dimensional tolerance, and surface finish. Use this for the fixed "
                "review pipeline: call it once per batch ID the user named, emitting all the "
                "calls together in the same turn, then pass every result to "
                "run_cross_batch_defect_trend."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"batch_id": {"type": "string", "description": "Exact batch ID, e.g. 'BATCH-101'."}},
                "required": ["batch_id"],
            },
        },
        "implementation": _inspect_batch,
    },
    {
        "schema": {
            "name": "run_cross_batch_defect_trend",
            "description": (
                "Analyze the COMPLETE prior inspect_batch results together for a cross-batch "
                "pattern (e.g. a shift correlation). Pass every finding explicitly — this tool "
                "has no access to prior inspect_batch results on its own. Use this once you've "
                "inspected every batch the user named; this is the integration pass that closes "
                "out the fixed pipeline."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "findings": {
                        "type": "array",
                        "description": "The complete prior inspect_batch result objects to analyze together.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "batch_id": {"type": "string"},
                                "shift": {"type": "string"},
                                "defect_count": {"type": "integer"},
                                "dimensional_tolerance_ok": {"type": "boolean"},
                                "surface_finish_ok": {"type": "boolean"},
                            },
                        },
                    },
                },
                "required": ["findings"],
            },
        },
        "implementation": _run_cross_batch_defect_trend,
    },
    {
        "schema": {
            "name": "scope_customer_defect_report",
            "description": (
                "Run an initial broad scope across every possible root-cause area (materials, "
                "calibration, process_step, packaging) for a customer-reported product defect. "
                "Returns which areas actually look suspicious — use this FIRST for any "
                "open-ended defect investigation (no specific batch IDs given), before deciding "
                "which areas warrant investigate_root_cause."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"product_id": {"type": "string", "description": "Exact product ID, e.g. 'PRODUCT-A'."}},
                "required": ["product_id"],
            },
        },
        "implementation": _scope_customer_defect_report,
    },
    {
        "schema": {
            "name": "investigate_root_cause",
            "description": (
                "Deep-dive into ONE root-cause area for a product defect. Only call this for "
                "areas that scope_customer_defect_report actually flagged — do not call it for "
                "every possible area, and do not skip an area the scope flagged."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string", "description": "Exact product ID, e.g. 'PRODUCT-A'."},
                    "area": {
                        "type": "string",
                        "enum": ROOT_CAUSE_AREAS,
                        "description": "The specific flagged area to investigate.",
                    },
                },
                "required": ["product_id", "area"],
            },
        },
        "implementation": _investigate_root_cause,
    },
]
