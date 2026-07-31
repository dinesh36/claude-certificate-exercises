"""
Task 5: Batch Processing Strategies
Domain: Prompt Engineering & Structured Output

A legal team's weekly vendor-contract renewal-risk audit, run on the Message
Batches API — a latency-tolerant workload submitted Friday evening for a
Monday-morning deadline. Contrasted with a synchronous call for an urgent,
blocking review during a live negotiation call, where there's no 24-hour
window to spare.

One contract's request is deliberately malformed by a real sizing bug (see
_buggy_max_tokens_for), so the run demonstrates detecting a batch failure by
custom_id and resubmitting only that document with a fix — not a staged
failure with no real cause.

See batch.py for the Batches API mechanics and data.py for the sample
contracts.
"""

import sys
from datetime import datetime

from common.client import DEFAULT_MODEL, get_client

from batch import build_request, collect_results, poll_until_ended, submit_batch
from data import CONTRACTS, DEADLINE_AT, SUBMITTED_AT, URGENT_REVIEW_CONTRACT

client = get_client()

SYSTEM_PROMPT = (
    "You are a contracts analyst flagging renewal risk. In 1-2 sentences, name any "
    "auto-renewal trap (a short opt-out window) or one-sided pricing clause. If the "
    "contract has neither, say so in one sentence."
)


def _buggy_max_tokens_for(document_text: str) -> int:
    """Reserves 200 response tokens per paragraph break, assuming every
    contract has at least one blank-line paragraph break the intake step
    inserted. Titan's amendment is a single line with none: paragraph_count
    is 1, so (paragraph_count - 1) rounds the budget all the way to zero."""
    paragraph_count = document_text.count("\n\n") + 1
    return 200 * (paragraph_count - 1)


def _fixed_max_tokens_for(document_text: str) -> int:
    """The fix: the same per-paragraph scaling, under a sane floor — so a
    document with no paragraph breaks still gets a workable response budget
    instead of an invalid, zero-token request."""
    paragraph_count = document_text.count("\n\n") + 1
    return max(300, 200 * (paragraph_count - 1))


def hours_between(start_iso: str, end_iso: str) -> float:
    return (datetime.fromisoformat(end_iso) - datetime.fromisoformat(start_iso)).total_seconds() / 3600


def meets_batch_sla(hours_until_deadline: float, batch_window_hours: float = 24) -> tuple[bool, float]:
    """Whether submitting now leaves enough room for the batch's up-to-24-hour
    window, with no guaranteed latency SLA of its own — and by how much."""
    margin = hours_until_deadline - batch_window_hours
    return margin >= 0, margin


def max_submission_interval_hours(
    sla_hours: float, batch_window_hours: float = 24, buffer_hours: float = 2
) -> float:
    """How often a batch must be submitted, on a recurring schedule, to
    guarantee no request waits longer than sla_hours end to end.

    Worst case, a request arriving just after one submission waits a full
    submission interval before it's picked up, then up to batch_window_hours
    to finish, plus buffer_hours of slack for retrieval and downstream work.
    Solving for the interval with the task statement's own numbers
    (30-hour SLA, 24-hour batch window, 2-hour buffer) gives 4 hours.
    """
    return sla_hours - batch_window_hours - buffer_hours


def run_prompt_refinement_check() -> None:
    """Sanity-checks the prompt on one representative contract with a plain
    synchronous call before committing the whole batch to it — cheap to fix
    now, expensive to discover after a 24-hour batch run comes back wrong."""
    sample_text = CONTRACTS["northwind"]
    response = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=200,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": sample_text}],
    )
    finding = next((block.text for block in response.content if block.type == "text"), "")
    print("Prompt refinement check (sample: northwind):")
    print(f"  {finding}\n")


def run_weekly_batch_audit() -> None:
    hours_available = hours_between(SUBMITTED_AT, DEADLINE_AT)
    ok, margin = meets_batch_sla(hours_available)
    print(
        f"Submitting {SUBMITTED_AT} for a {DEADLINE_AT} deadline: "
        f"{hours_available:.1f}h available, {'OK' if ok else 'NOT ENOUGH TIME'} "
        f"(margin {margin:+.1f}h over the batch window)."
    )
    interval = max_submission_interval_hours(sla_hours=30, batch_window_hours=24, buffer_hours=2)
    print(f"Worked example: a 30-hour SLA with a 24-hour batch window and a 2-hour buffer needs "
          f"submissions every <= {interval:.0f}h.\n")

    requests = [
        build_request(f"contract-{name}", DEFAULT_MODEL, SYSTEM_PROMPT, text, _buggy_max_tokens_for(text))
        for name, text in CONTRACTS.items()
    ]
    batch = submit_batch(client, requests)
    print(f"Submitted batch {batch.id} ({len(requests)} contracts).")
    batch = poll_until_ended(client, batch.id)

    succeeded, failed = collect_results(client, batch.id)
    print(f"\nFirst pass: {len(succeeded)} succeeded, {len(failed)} failed.")
    for custom_id, reason in failed.items():
        print(f"  {custom_id} failed: {reason}")

    if failed:
        print("\nResubmitting only the failed contract(s), with the sizing bug fixed:")
        retry_requests = [
            build_request(custom_id, DEFAULT_MODEL, SYSTEM_PROMPT, CONTRACTS[custom_id.removeprefix("contract-")],
                          _fixed_max_tokens_for(CONTRACTS[custom_id.removeprefix("contract-")]))
            for custom_id in failed
        ]
        retry_batch = submit_batch(client, retry_requests)
        print(f"  submitted retry batch {retry_batch.id} ({len(retry_requests)} contract(s)).")
        retry_batch = poll_until_ended(client, retry_batch.id)
        retry_succeeded, retry_failed = collect_results(client, retry_batch.id)
        succeeded.update(retry_succeeded)
        if retry_failed:
            print(f"  still failing after retry: {retry_failed}")

    print("\nFinal audit findings:")
    for custom_id, finding in succeeded.items():
        print(f"  {custom_id}: {finding}")


def run_urgent_sync_review() -> None:
    """The blocking counter-example: reviewed synchronously because the
    vendor is on the phone right now, not queued into next week's batch."""
    response = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=200,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": URGENT_REVIEW_CONTRACT}],
    )
    finding = next((block.text for block in response.content if block.type == "text"), "")
    print("Urgent synchronous review (live negotiation call):")
    print(f"  {finding}")


def main(mode: str = "batch") -> None:
    if mode == "urgent":
        run_urgent_sync_review()
        return

    run_prompt_refinement_check()
    run_weekly_batch_audit()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "batch")
