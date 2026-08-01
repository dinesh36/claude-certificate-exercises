#!/usr/bin/env python3
"""Human-review routing and confidence calibration over BrightPath Talent's
resume-screening validation set (Domain 5, Task Statement 5.5).

Reads the labeled validation set and today's incoming extraction queue from
data.py, then: measures aggregate vs. segment-level accuracy, draws a
stratified sample of high-confidence extractions for ongoing QA, calibrates
a per-segment auto-approve confidence threshold against the labeled data,
and routes today's queue to auto-approve or human review under limited
reviewer capacity. One live headless Claude Code call demonstrates the
model actually producing a field-level confidence score, rather than
assuming every confidence number in the mock data was real.
"""

import json
import random
import re
import subprocess
from collections import defaultdict

from data import TODAYS_QUEUE, VALIDATION_SET, SAMPLE_TRANSCRIPT_EXCERPT

TARGET_PRECISION = 0.98
HIGH_CONFIDENCE_THRESHOLD = 0.90
REVIEWER_CAPACITY = 5


def aggregate_accuracy(records):
    return sum(1 for r in records if r["is_correct"]) / len(records)


def accuracy_by_segment(records):
    buckets = defaultdict(list)
    for r in records:
        buckets[(r["document_type"], r["field"])].append(r["is_correct"])
    return {seg: sum(vals) / len(vals) for seg, vals in buckets.items()}


def stratified_sample_high_confidence(records, per_stratum=3, seed=7):
    """Draw a fixed-size sample from each document-type stratum among
    high-confidence extractions, so ongoing QA audits every document type
    instead of being dominated by whichever type has the most volume."""
    rng = random.Random(seed)
    high_conf = [r for r in records if r["model_confidence"] >= HIGH_CONFIDENCE_THRESHOLD]
    by_type = defaultdict(list)
    for r in high_conf:
        by_type[r["document_type"]].append(r)
    sample = []
    for doc_type, items in by_type.items():
        sample.extend(rng.sample(items, min(per_stratum, len(items))))
    return sample


def calibrate_thresholds(records, target_precision=TARGET_PRECISION, min_subset_size=5):
    """For each (document_type, field) segment, find the lowest confidence
    threshold whose auto-approved subset meets target_precision on the
    labeled validation set. A segment that can't reach it at any threshold
    is marked 'always_review' rather than assigned a meaningless cutoff.

    Thresholds are only accepted if at least `min_subset_size` validation
    records support them — otherwise a single lucky high-confidence record
    (e.g. one correct extraction at the top confidence value) can produce a
    100%-precision subset of size 1 and pass an arbitrarily strict target,
    which is a sampling artifact, not a calibrated threshold."""
    segments = defaultdict(list)
    for r in records:
        segments[(r["document_type"], r["field"])].append(r)

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


def get_model_confidence_extraction(document_text, field):
    """Real headless Claude Code call: ask the model to extract one field and
    self-report a confidence score. On failure, returns a structured error
    (errorCategory/isRetryable/description) instead of silently defaulting
    to a made-up confidence value — per this repo's tool-error convention."""
    prompt = (
        f"Extract the '{field}' value from this interview transcript excerpt and report your "
        f"confidence (0.0-1.0) that the extraction is correct. Respond with ONLY a JSON object "
        f'of the shape {{"field": "...", "value": "...", "confidence": 0.0}} and nothing else.\n\n'
        f"Transcript excerpt:\n{document_text}"
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


def _parse_json_object(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def route_todays_queue(queue, thresholds, capacity=REVIEWER_CAPACITY):
    needs_review = []
    auto_approved = []
    for item in queue:
        seg = (item["document_type"], item["field"])
        threshold = thresholds.get(seg, "always_review")
        reasons = []
        if threshold == "always_review":
            reasons.append(f"segment {seg} never reaches {TARGET_PRECISION:.0%} precision on the validation set")
        elif item["model_confidence"] < threshold:
            reasons.append(f"confidence {item['model_confidence']} below calibrated threshold {threshold}")
        if item.get("ambiguous_source"):
            reasons.append("source document flagged ambiguous/contradictory")
        if reasons:
            needs_review.append({**item, "reasons": reasons})
        else:
            auto_approved.append(item)

    needs_review.sort(key=lambda r: r["model_confidence"])
    reviewed_now = needs_review[:capacity]
    deferred = needs_review[capacity:]
    return auto_approved, reviewed_now, deferred


def main():
    print("=== Aggregate accuracy (validation set) ===")
    print(f"{aggregate_accuracy(VALIDATION_SET):.1%} across {len(VALIDATION_SET)} extractions\n")

    print("=== Accuracy by document type + field (worst first) ===")
    by_segment = accuracy_by_segment(VALIDATION_SET)
    for seg, acc in sorted(by_segment.items(), key=lambda kv: kv[1]):
        flag = "  <-- hidden problem, masked by the aggregate above" if acc < 0.75 else ""
        print(f"{seg[0]:22s} {seg[1]:20s} {acc:.1%}{flag}")

    print("\n=== Stratified sample of high-confidence extractions (ongoing QA) ===")
    for r in stratified_sample_high_confidence(VALIDATION_SET):
        print(f"{r['document_id']} {r['document_type']:22s} {r['field']:20s} conf={r['model_confidence']} correct={r['is_correct']}")

    print(f"\n=== Calibrated per-segment auto-approve thresholds (target precision {TARGET_PRECISION:.0%}) ===")
    thresholds = calibrate_thresholds(VALIDATION_SET)
    for seg, t in sorted(thresholds.items()):
        print(f"{seg[0]:22s} {seg[1]:20s} -> {t}")

    print("\n=== Live model confidence extraction (real claude -p call) ===")
    live_result = get_model_confidence_extraction(SAMPLE_TRANSCRIPT_EXCERPT, "years_experience")
    print(json.dumps(live_result, indent=2))

    print(f"\n=== Routing today's queue (reviewer capacity = {REVIEWER_CAPACITY}) ===")
    auto_approved, reviewed_now, deferred = route_todays_queue(TODAYS_QUEUE, thresholds)

    print(f"Auto-approved ({len(auto_approved)}):")
    for r in auto_approved:
        print(f"  {r['document_id']} {r['document_type']}/{r['field']} conf={r['model_confidence']}")

    print(f"Sent to review now ({len(reviewed_now)}):")
    for r in reviewed_now:
        print(f"  {r['document_id']} {r['document_type']}/{r['field']} conf={r['model_confidence']} — {'; '.join(r['reasons'])}")

    print(f"Deferred, reviewer capacity exceeded ({len(deferred)}):")
    for r in deferred:
        print(f"  {r['document_id']} {r['document_type']}/{r['field']} conf={r['model_confidence']} — {'; '.join(r['reasons'])}")


if __name__ == "__main__":
    main()
