"""Structured tool error responses (Domain 2).

Every tool error returned to the model carries errorCategory, isRetryable,
and a human-readable description instead of a generic failure string.
"""

from typing import Literal

ErrorCategory = Literal["transient", "validation", "permission"]


def tool_error(error_category: ErrorCategory, is_retryable: bool, description: str) -> dict:
    return {
        "errorCategory": error_category,
        "isRetryable": is_retryable,
        "description": description,
    }


def is_tool_error(result: object) -> bool:
    return isinstance(result, dict) and "errorCategory" in result
