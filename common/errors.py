"""Structured tool error responses (Domain 2).

Every tool error returned to the model carries errorCategory, isRetryable,
and a human-readable description instead of a generic failure string.
"""

import json
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


class StructuredToolError(Exception):
    """Raise from an MCP tool implementation to surface a `tool_error()` dict
    through FastMCP's isError mechanism, instead of a bare failure string.

    FastMCP turns any raised exception into an isError=true tool result whose
    content is the exception's string — this exception's string is the
    JSON-serialized error dict, so the agent can parse errorCategory/
    isRetryable/description back out of it rather than getting only free text.
    A business-rule violation (e.g. a policy limit) uses errorCategory
    "validation" — there is no separate "business" category; see
    ErrorCategory above.
    """

    def __init__(self, error_category: ErrorCategory, is_retryable: bool, description: str):
        super().__init__(json.dumps(tool_error(error_category, is_retryable, description)))
