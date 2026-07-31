"""Task 5: Batch Processing Strategies
Prompt Engineering & Structured Output
Message Batches API mechanics: build, submit, poll, and retrieve results
keyed by custom_id — the correlation field a batch's request/response pairs
share, since responses can arrive in any order.

No request built here ever carries a `tools=` parameter. The Batch API
can't pause mid-request to execute a tool and return control — a workload
that genuinely needs multi-turn tool calling has to run through the
synchronous API's agentic loop instead, one document at a time.
"""

import time

from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request


def build_request(custom_id: str, model: str, system: str, document_text: str, max_tokens: int) -> Request:
    return Request(
        custom_id=custom_id,
        params=MessageCreateParamsNonStreaming(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": document_text}],
        ),
    )


def submit_batch(client, requests: list[Request]):
    return client.messages.batches.create(requests=requests)


def poll_until_ended(client, batch_id: str, interval_seconds: int = 20):
    """Blocks until the batch's processing_status is "ended".

    There's no guaranteed latency SLA on the Batch API — this loop has no
    timeout of its own, since a caller with a real deadline is exactly the
    scenario the SLA-margin calculation in main.py exists to check before
    ever submitting, not something to enforce here.
    """
    while True:
        batch = client.messages.batches.retrieve(batch_id)
        if batch.processing_status == "ended":
            return batch
        print(
            f"  ...batch {batch_id} still {batch.processing_status} "
            f"(succeeded={batch.request_counts.succeeded}, "
            f"errored={batch.request_counts.errored}, "
            f"processing={batch.request_counts.processing})"
        )
        time.sleep(interval_seconds)


def collect_results(client, batch_id: str) -> tuple[dict[str, str], dict[str, str]]:
    """Splits a batch's results into (succeeded text by custom_id, failure reason by custom_id).

    Results arrive in any order — every result is matched back to its
    request by custom_id, never by position in the stream.
    """
    succeeded: dict[str, str] = {}
    failed: dict[str, str] = {}

    for result in client.messages.batches.results(batch_id):
        if result.result.type == "succeeded":
            message = result.result.message
            succeeded[result.custom_id] = next(
                (block.text for block in message.content if block.type == "text"), ""
            )
        elif result.result.type == "errored":
            # result.result.error is an envelope (ErrorResponse); the actual
            # type/message live one level deeper, on its own .error field.
            inner = result.result.error.error
            failed[result.custom_id] = f"{inner.type}: {inner.message}"
        else:
            # "canceled" or "expired" — not retried automatically; surfaced
            # the same as any other failure so the caller decides what to do.
            failed[result.custom_id] = result.result.type

    return succeeded, failed
