"""Pydantic validation and the retry-classification logic (Domain 4 Step 2).

ListingExtraction mirrors tools.py's EXTRACT_LISTING_TOOL schema exactly.
validate_extraction runs a raw tool_use.input dict through it; classify_error
tells the retry loop in main.py whether a given failure is retryable (a
format/shape mistake the model can fix on a second pass) or not (the source
document genuinely doesn't state the value, so the fix is a null field, not
a retry).
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field, ValidationError, model_validator

PropertyType = Literal["single_family", "condo", "townhouse", "multi_family", "other"]


class ListingExtraction(BaseModel):
    listing_id: str
    address: str
    price: float
    property_type: PropertyType
    property_type_other_detail: Optional[str] = None
    square_footage: Optional[int] = None
    year_built: Optional[int] = None
    hoa_fee_monthly: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    field_confidence: dict[str, float] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _other_requires_detail(self) -> "ListingExtraction":
        if self.property_type == "other" and not self.property_type_other_detail:
            raise ValueError(
                "property_type_other_detail is required (non-null) when property_type is 'other'."
            )
        if self.property_type != "other" and self.property_type_other_detail:
            raise ValueError(
                "property_type_other_detail must be null when property_type is not 'other'."
            )
        return self


def validate_extraction(raw: dict) -> tuple[Optional[ListingExtraction], Optional[str]]:
    """Returns (parsed, None) on success, or (None, error_message) on failure."""
    try:
        return ListingExtraction(**raw), None
    except ValidationError as exc:
        return None, str(exc)


# Substrings that mark a validation failure as a format/shape mistake the
# model can plausibly fix on retry -- as opposed to the source document
# genuinely not stating a value, where the fix is a null field, not a retry.
_RESOLVABLE_MARKERS = (
    "property_type_other_detail is required",
    "property_type_other_detail must be null",
    "Input should be a valid number",
    "Input should be",
    "enum",
)


def classify_error(error_message: str) -> Literal["resolvable", "unresolvable"]:
    """Heuristic used to log/report each retry outcome (Domain 4 Step 2's
    "track which errors are resolvable via retry ... versus which are not").
    A real run still always retries once regardless of this classification --
    it only changes how the outcome gets reported afterward."""
    return "resolvable" if any(marker in error_message for marker in _RESOLVABLE_MARKERS) else "unresolvable"
