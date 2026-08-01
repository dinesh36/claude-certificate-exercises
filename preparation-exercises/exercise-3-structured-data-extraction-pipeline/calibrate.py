"""Human-review routing and confidence calibration over NestList's labeled
listing-extraction validation set (Domain 5 Step 5).

Adapted from tasks/context-management/task-5-stratified-confidence-calibration/
calibrate.py's aggregate/segment/threshold/routing shape -- same functions,
same intent, applied to (source, field) segments instead of
(document_type, field).
"""

import json
import re
import subprocess
from collections import defaultdict

TARGET_PRECISION = 0.95
HIGH_CONFIDENCE_THRESHOLD = 0.90
REVIEWER_CAPACITY = 4


def aggregate_accuracy(records):
    return sum(1 for r in records if r["is_correct"]) / len(records)


def accuracy_by_segment(records):
    buckets = defaultdict(list)
    for r in records:
        buckets[(r["source"], r["field"])].append(r["is_correct"])
    return {seg: sum(vals) / len(vals) for seg, vals in buckets.items()}


def calibrate_thresholds(records, target_precision=TARGET_PRECISION, min_subset_size=5):
    """For each (source, field) segment, find the lowest confidence threshold
    whose auto-approved subset meets target_precision on the labeled
    validation set. A segment that can't reach it at any threshold is marked
    'always_review' rather than assigned a meaningless cutoff.

    Thresholds are only accepted if at least `min_subset_size` validation
    records support them -- otherwise a single lucky high-confidence record
    can produce a 100%-precision subset of size 1 and pass an arbitrarily
    strict target, which is a sampling artifact, not a calibrated threshold.
    """
    segments = defaultdict(list)
    for r in records:
        segments[(r["source"], r["field"])].append(r)

    thresholds = {}
    for seg, items in segments.items():
        candidates = sorted({r["model_confidence"] for r in items})
        chosen = None
        for candidate in candidates:
            subset = [r for r in items if r["model_confidence"] >= candidate]
            if len(subset) < min_subset_size:
                continue
            precision = sum(r["is_correct"] for r in subset) / len(subset)
            if precision >= target_precision:
                chosen = candidate
                break
        thresholds[seg] = chosen if chosen is not None else "always_review"
    return thresholds


def route_todays_queue(queue, thresholds, capacity=REVIEWER_CAPACITY):
    needs_review = []
    auto_approved = []
    for item in queue:
        seg = (item["source"], item["field"])
        threshold = thresholds.get(seg, "always_review")
        reasons = []
        if threshold == "always_review":
            reasons.append(f"segment {seg} never reaches {TARGET_PRECISION:.0%} precision on the validation set")
        elif item["model_confidence"] < threshold:
            reasons.append(f"confidence {item['model_confidence']} below calibrated threshold {threshold}")
        if item.get("ambiguous_source"):
            reasons.append("source document flagged ambiguous/unreadable")
        if reasons:
            needs_review.append({**item, "reasons": reasons})
        else:
            auto_approved.append(item)

    needs_review.sort(key=lambda r: r["model_confidence"])
    reviewed_now = needs_review[:capacity]
    deferred = needs_review[capacity:]
    return auto_approved, reviewed_now, deferred


def _parse_json_object(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def get_live_confidence_extraction(document_text: str, field: str) -> dict:
    """Real headless Claude Code call: ask the model to extract one field and
    self-report a confidence score. On failure, returns a structured error
    (errorCategory/isRetryable/description) instead of silently defaulting
    to a made-up confidence value -- per this repo's tool-error convention."""
    prompt = (
        f"Extract the '{field}' value from this real-estate listing description and report your "
        f"confidence (0.0-1.0) that the extraction is correct. Respond with ONLY a JSON object of "
        f'the shape {{"field": "...", "value": "...", "confidence": 0.0}} and nothing else.\n\n'
        f"Listing:\n{document_text}"
    )
    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--output-format", "json"],
            capture_output=True,
            text=True,
            timeout=90,
            check=True,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as exc:
        return {
            "errorCategory": "transient",
            "isRetryable": True,
            "description": f"claude -p invocation failed: {exc}",
        }

    try:
        envelope = json.loads(result.stdout)
        return _parse_json_object(envelope["result"])
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        return {
            "errorCategory": "validation",
            "isRetryable": False,
            "description": f"claude -p did not return the expected JSON extraction shape: {exc}",
        }
