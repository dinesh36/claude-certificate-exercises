"""Tests for workers.py's job-processing functions."""

from core import enqueue_task
from workers import process_email_job, process_report_job


def test_process_email_job_reports_recipient():
    enqueue_task("send_email", {"to": "a@example.com"})
    assert "a@example.com" in process_email_job()


def test_process_report_job_reports_name():
    enqueue_task("build_report", {"report": "daily"})
    assert "daily" in process_report_job()
