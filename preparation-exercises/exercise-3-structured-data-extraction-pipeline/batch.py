"""Message Batches API mechanics for the listing-intake pipeline (Domain 4 Step 4).

Same build/submit/poll/collect shape as
tasks/prompt-engineering/task-5-batch-processing-strategies/batch.py -- every
request here carries `tools=[EXTRACT_LISTING_TOOL]` and a forced
`tool_choice`, since a batch request is still just one Messages API call per
document; the Batch API itself has no tool-use-specific behavior of its own.
"""

import time

from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

from tools import EXTRACT_LISTING_TOOL


def build_request(custom_id: str, model: str, system: str, document_text: str, max_tokens: int) -> Request:
    return Request(
        custom_id=custom_id,
        params=MessageCreateParamsNonStreaming(
            model=model,
            max_tokens=max_tokens,
            system=system,
            tools=[EXTRACT_LISTING_TOOL],
            tool_choice={"type": "tool", "name": "extract_listing"},
            messages=[{"role": "user", "content": document_text}],
        ),
    )


def submit_batch(client, requests: list[Request]):
    return client.messages.batches.create(requests=requests)


def poll_until_ended(client, batch_id: str, interval_seconds: int = 20):
    """Blocks until the batch's processing_status is "ended". No timeout of
    its own -- a caller with a real deadline checks that separately, via the
    SLA-margin math in main.py, before ever submitting."""
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


def collect_results(client, batch_id: str) -> tuple[dict[str, dict], dict[str, str]]:
    """Splits a batch's results into (extracted tool_use.input by custom_id,
    failure reason by custom_id). Results arrive in any order -- every result
    is matched back to its request by custom_id, never by position."""
    succeeded: dict[str, dict] = {}
    failed: dict[str, str] = {}

    for result in client.messages.batches.results(batch_id):
        if result.result.type == "succeeded":
            message = result.result.message
            tool_use = next((block for block in message.content if block.type == "tool_use"), None)
            if tool_use is None:
                failed[result.custom_id] = "No tool_use block in the response -- model returned plain text instead."
            else:
                succeeded[result.custom_id] = tool_use.input
        elif result.result.type == "errored":
            # result.result.error is an envelope (ErrorResponse); the actual
            # type/message live one level deeper, on its own .error field.
            inner = result.result.error.error
            failed[result.custom_id] = f"{inner.type}: {inner.message}"
        else:
            # "canceled" or "expired" -- not retried automatically; surfaced
            # the same as any other failure so the caller decides what to do.
            failed[result.custom_id] = result.result.type

    return succeeded, failed
