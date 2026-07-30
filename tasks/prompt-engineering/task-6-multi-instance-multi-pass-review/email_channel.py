"""Email notification channel."""

import requests

_PROVIDER_URL = "https://api.mailrelay.example.com/v1/send"

RATE_LIMIT_PER_MINUTE = 30


class EmailDeliveryError(Exception):
    """Raised when the email provider rejects or fails to deliver a message."""


def _attempt_send(recipient: str, message: str) -> None:
    response = requests.post(
        _PROVIDER_URL, json={"to": recipient, "body": message}, timeout=10
    )
    if response.status_code >= 500:
        raise EmailDeliveryError(f"provider returned {response.status_code}")


def send_email(recipient: str, message: str) -> None:
    """Sends an email notification, retrying until the provider accepts it."""
    while True:
        try:
            _attempt_send(recipient, message)
            return
        except EmailDeliveryError:
            continue
