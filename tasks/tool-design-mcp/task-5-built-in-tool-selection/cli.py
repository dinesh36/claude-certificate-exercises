"""Command-line entry point for the task-queue demo."""

from compat import add_job
from core import enqueue_task
from workers import process_email_job, process_report_job


def main() -> None:
    add_job("send_email", {"to": "ops@example.com"})
    enqueue_task("build_report", {"report": "weekly-summary"})
    print(process_email_job())
    print(process_report_job())


if __name__ == "__main__":
    main()
