"""
Preparation Exercise 3: Build a Structured Data Extraction Pipeline
Domains reinforced: 4 (Prompt Engineering & Structured Output), 5 (Context Management & Reliability)

NestList's real-estate listing-intake pipeline: forces tool_use extraction
against a JSON schema with required/optional/enum-other/nullable fields,
retries validation failures with the specific error fed back, uses real
few-shot conversation turns (not prose examples) to teach two source
formats before testing a third, unseen one, submits a weekly listing
data-quality batch via the Message Batches API, and calibrates confidence-
based human-review routing against a labeled validation set.

See tools.py for the schema, validation.py for the Pydantic model + retry
classification, batch.py for the Batches API mechanics, calibrate.py for the
confidence-routing analysis, and data.py for every sample/mock input.
"""

import json
import re
import sys
from datetime import datetime

from common.client import DEFAULT_MODEL, get_client

from batch import build_request, collect_results, poll_until_ended, submit_batch
from calibrate import (
    REVIEWER_CAPACITY,
    TARGET_PRECISION,
    accuracy_by_segment,
    aggregate_accuracy,
    calibrate_thresholds,
    get_live_confidence_extraction,
    route_todays_queue,
)
from data import (
    BATCH_DEADLINE_AT,
    BATCH_LISTINGS,
    BATCH_SUBMITTED_AT,
    FEW_SHOT_MLS_EXTRACTION,
    FEW_SHOT_MLS_SHEET,
    FEW_SHOT_NARRATIVE,
    FEW_SHOT_NARRATIVE_EXTRACTION,
    SAMPLE_NARRATIVE_FOR_LIVE_CHECK,
    TEST_NARRATIVE_UNSEEN,
    TODAYS_QUEUE,
    VALIDATION_SET,
)
from tools import EXTRACT_LISTING_TOOL
from validation import classify_error, validate_extraction

client = get_client()

SYSTEM_PROMPT = (
    "You extract structured data from real-estate listing submissions for NestList, an MLS "
    "aggregator. Source documents vary in format -- structured MLS feed sheets and narrative "
    "agent descriptions both occur. Never fabricate a value the source document doesn't state; "
    "use null instead."
)


def _few_shot_messages() -> list[dict]:
    """Two worked examples as real conversation turns (user doc -> assistant
    tool_use -> tool_result), not prose descriptions -- so the few-shot
    demonstration exercises tool_use the same way the real extraction call
    does (Step 3)."""
    return [
        {"role": "user", "content": FEW_SHOT_MLS_SHEET},
        {
            "role": "assistant",
            "content": [
                {"type": "tool_use", "id": "toolu_fewshot_mls", "name": "extract_listing", "input": FEW_SHOT_MLS_EXTRACTION}
            ],
        },
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "toolu_fewshot_mls", "content": "Recorded."}]},
        {"role": "user", "content": FEW_SHOT_NARRATIVE},
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_fewshot_narrative",
                    "name": "extract_listing",
                    "input": FEW_SHOT_NARRATIVE_EXTRACTION,
                }
            ],
        },
        {
            "role": "user",
            "content": [{"type": "tool_result", "tool_use_id": "toolu_fewshot_narrative", "content": "Recorded."}],
        },
    ]


def extract_with_retry(document_text: str, max_retries: int = 1) -> dict:
    """Steps 1-3: forced tool_choice extraction with real few-shot history,
    retried once with the specific validation error fed back if the first
    attempt doesn't parse. Returns a report dict, never raises."""
    messages = _few_shot_messages() + [{"role": "user", "content": document_text}]

    attempt = 0
    last_error = None
    while True:
        response = client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=[EXTRACT_LISTING_TOOL],
            tool_choice={"type": "tool", "name": "extract_listing"},
            messages=messages,
        )
        tool_use = next((block for block in response.content if block.type == "tool_use"), None)
        if tool_use is None:
            last_error = "No tool_use block in the response."
            classification = "unresolvable"
        else:
            parsed, error = validate_extraction(tool_use.input)
            if parsed is not None:
                return {"status": "extracted", "attempts": attempt + 1, "extraction": parsed.model_dump()}
            last_error = error
            classification = classify_error(error)

        if attempt == max_retries:
            return {"status": "failed", "attempts": attempt + 1, "error": last_error, "classification": classification}

        print(f"  attempt {attempt + 1} failed validation ({classification}): {last_error}")
        messages += [
            {
                "role": "assistant",
                "content": [{"type": "tool_use", "id": tool_use.id, "name": "extract_listing", "input": tool_use.input}],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": (
                            f"That extraction failed validation: {last_error}\n"
                            f"Original document:\n{document_text}\n"
                            "Call extract_listing again with a corrected extraction."
                        ),
                        "is_error": True,
                    }
                ],
            },
        ]
        attempt += 1


def hours_between(start_iso: str, end_iso: str) -> float:
    return (datetime.fromisoformat(end_iso) - datetime.fromisoformat(start_iso)).total_seconds() / 3600


def meets_batch_sla(hours_until_deadline: float, batch_window_hours: float = 24) -> tuple[bool, float]:
    """Whether submitting now leaves enough room for the batch's up-to-24-hour
    window, with no guaranteed latency SLA of its own -- and by how much."""
    margin = hours_until_deadline - batch_window_hours
    return margin >= 0, margin


def _buggy_max_tokens_for(document_text: str) -> int:
    """Reserves 150 response tokens per numeric mention (price, sqft, year,
    etc.) in the document, assuming every listing states at least two such
    numbers. listing-40303 states only one ("$199,000") -- (1 - 1) * 150
    rounds the budget all the way to zero, an invalid max_tokens value the
    API genuinely rejects."""
    numeric_mentions = len(re.findall(r"\$?\d[\d,]*", document_text))
    return 150 * (numeric_mentions - 1)


def _fixed_max_tokens_for(document_text: str) -> int:
    """The fix: the same per-mention scaling, under a sane floor -- so a
    terse document still gets a workable response budget instead of an
    invalid, zero-token request."""
    numeric_mentions = len(re.findall(r"\$?\d[\d,]*", document_text))
    return max(300, 150 * (numeric_mentions - 1))


def run_extraction_demo() -> None:
    print("=== Single-document extraction (unseen narrative listing, generalization check) ===")
    result = extract_with_retry(TEST_NARRATIVE_UNSEEN)
    print(json.dumps(result, indent=2))


def run_batch_demo() -> None:
    hours_available = hours_between(BATCH_SUBMITTED_AT, BATCH_DEADLINE_AT)
    ok, margin = meets_batch_sla(hours_available)
    print(
        f"Submitting {BATCH_SUBMITTED_AT} for a {BATCH_DEADLINE_AT} weekly data-quality review: "
        f"{hours_available:.1f}h available, {'OK' if ok else 'NOT ENOUGH TIME'} "
        f"(margin {margin:+.1f}h over the batch window).\n"
    )

    requests = [
        build_request(cid, DEFAULT_MODEL, SYSTEM_PROMPT, text, _buggy_max_tokens_for(text))
        for cid, text in BATCH_LISTINGS.items()
    ]
    batch = submit_batch(client, requests)
    print(f"Submitted batch {batch.id} ({len(requests)} listings).")
    started = datetime.now()
    batch = poll_until_ended(client, batch.id)
    elapsed_seconds = (datetime.now() - started).total_seconds()

    succeeded, failed = collect_results(client, batch.id)
    print(f"\nFirst pass: {len(succeeded)} succeeded, {len(failed)} failed.")
    for custom_id, reason in failed.items():
        print(f"  {custom_id} failed: {reason}")

    if failed:
        print("\nResubmitting only the failed listing(s), with the sizing bug fixed:")
        retry_requests = [
            build_request(cid, DEFAULT_MODEL, SYSTEM_PROMPT, BATCH_LISTINGS[cid], _fixed_max_tokens_for(BATCH_LISTINGS[cid]))
            for cid in failed
        ]
        retry_batch = submit_batch(client, retry_requests)
        print(f"  submitted retry batch {retry_batch.id} ({len(retry_requests)} listing(s)).")
        retry_batch = poll_until_ended(client, retry_batch.id)
        retry_succeeded, retry_failed = collect_results(client, retry_batch.id)
        succeeded.update(retry_succeeded)
        if retry_failed:
            print(f"  still failing after retry: {retry_failed}")

    print(f"\nBatch of {len(BATCH_LISTINGS)} finished in {elapsed_seconds:.0f}s.")
    per_doc = elapsed_seconds / len(BATCH_LISTINGS)
    extrapolated_hours = (per_doc * 100) / 3600
    print(
        f"Back-of-envelope extrapolation to a full 100-listing weekly batch: ~{per_doc:.1f}s/listing "
        f"measured here -> ~{extrapolated_hours:.2f}h for 100, comfortably inside the "
        f"{hours_available:.0f}h window (the Batch API gives no per-document latency guarantee -- "
        "this is a planning estimate, not a promise)."
    )

    print("\nFinal extracted listings:")
    for custom_id, extraction in succeeded.items():
        print(f"  {custom_id}: {extraction}")


def run_calibration_demo() -> None:
    print("=== Aggregate accuracy (validation set) ===")
    print(f"{aggregate_accuracy(VALIDATION_SET):.1%} across {len(VALIDATION_SET)} extractions\n")

    print("=== Accuracy by source + field (worst first) ===")
    by_segment = accuracy_by_segment(VALIDATION_SET)
    for seg, acc in sorted(by_segment.items(), key=lambda kv: kv[1]):
        flag = "  <-- hidden problem, masked by the aggregate above" if acc < 0.75 else ""
        print(f"{seg[0]:10s} {seg[1]:16s} {acc:.1%}{flag}")

    print(f"\n=== Calibrated per-segment auto-approve thresholds (target precision {TARGET_PRECISION:.0%}) ===")
    thresholds = calibrate_thresholds(VALIDATION_SET)
    for seg, t in sorted(thresholds.items()):
        print(f"{seg[0]:10s} {seg[1]:16s} -> {t}")

    print("\n=== Live model confidence extraction (real claude -p call) ===")
    live_result = get_live_confidence_extraction(SAMPLE_NARRATIVE_FOR_LIVE_CHECK, "square_footage")
    print(json.dumps(live_result, indent=2))

    print(f"\n=== Routing today's queue (reviewer capacity = {REVIEWER_CAPACITY}) ===")
    auto_approved, reviewed_now, deferred = route_todays_queue(TODAYS_QUEUE, thresholds)
    print(f"Auto-approved ({len(auto_approved)}):")
    for r in auto_approved:
        print(f"  {r['document_id']} {r['source']}/{r['field']} conf={r['model_confidence']}")
    print(f"Sent to review now ({len(reviewed_now)}):")
    for r in reviewed_now:
        print(f"  {r['document_id']} {r['source']}/{r['field']} conf={r['model_confidence']} - {'; '.join(r['reasons'])}")
    print(f"Deferred, reviewer capacity exceeded ({len(deferred)}):")
    for r in deferred:
        print(f"  {r['document_id']} {r['source']}/{r['field']} conf={r['model_confidence']} - {'; '.join(r['reasons'])}")


def main(mode: str = "all") -> None:
    if mode in ("all", "extract"):
        run_extraction_demo()
        print()
    if mode in ("all", "batch"):
        run_batch_demo()
        print()
    if mode in ("all", "calibrate"):
        run_calibration_demo()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "all")
