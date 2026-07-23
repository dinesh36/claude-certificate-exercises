"""Worker functions that pull jobs off the queue and process them."""

import logging

from core import QueueEmptyError, dequeue_task

logger = logging.getLogger(__name__)


def process_email_job() -> str:
    """Pull one job off the queue and send it as an email notification."""
    try:
        job = dequeue_task()
    except QueueEmptyError:
        return "no email jobs waiting"
    try:
        recipient = job["payload"]["to"]
        return f"sent email to {recipient}"
    except Exception as exc:
        logger.error("job failed: %s", exc)
        raise


def process_report_job() -> str:
    """Pull one job off the queue and generate a report from it."""
    try:
        job = dequeue_task()
    except QueueEmptyError:
        return "no report jobs waiting"
    try:
        report_name = job["payload"]["report"]
        return f"generated report {report_name}"
    except Exception as exc:
        logger.error("job failed: %s", exc)
        raise
