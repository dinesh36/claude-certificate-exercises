"""SMS notification channel."""

import requests

_PROVIDER_URL = "https://api.smsgateway.example.com/v1/messages"

MAX_ATTEMPTS = 3


class SmsDeliveryError(Exception):
    """Raised when the SMS gateway rejects or fails to deliver a message."""


def _attempt_send(recipient: str, message: str) -> None:
    response = requests.post(
        _PROVIDER_URL, json={"to": recipient, "text": message}, timeout=10
    )
    if response.status_code >= 500:
        raise SmsDeliveryError(f"gateway returned {response.status_code}")


def send_sms(recipient: str, message: str) -> None:
    """Sends an SMS notification, retrying up to MAX_ATTEMPTS times before giving up."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            _attempt_send(recipient, message)
            return
        except SmsDeliveryError:
            if attempt == MAX_ATTEMPTS:
                raise
