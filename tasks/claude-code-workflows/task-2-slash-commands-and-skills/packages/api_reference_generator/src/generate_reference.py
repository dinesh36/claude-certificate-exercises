"""Generates API reference content from the live endpoint registry.

This is the source of truth `api-ref-sync` compares the hand-written
pages in packages/docs_site/pages/ against.
"""

ENDPOINTS = [
    {"method": "POST", "path": "/v2/reports", "summary": "Create a new report."},
    {"method": "GET", "path": "/v2/reports/{id}", "summary": "Retrieve a report by id."},
]
