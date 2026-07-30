"""Fans a notification out to every channel, respecting each channel's own rate limit."""

import time

import email_channel
import sms_channel

_CHANNELS = (
    (email_channel, email_channel.send_email),
    (sms_channel, sms_channel.send_sms),
)

_last_sent_at: dict = {}


def _within_rate_limit(channel_module, now: float) -> bool:
    """A channel is throttled if we sent through it more recently than its own rate window."""
    limit_per_minute = getattr(channel_module, "RATE_LIMIT_PER_MINUTE", None)
    if limit_per_minute is None:
        # No rate limit configured for this channel - nothing to enforce.
        return True

    last_sent = _last_sent_at.get(channel_module)
    if last_sent is None:
        return True

    seconds_per_message = 60.0 / limit_per_minute
    return (now - last_sent) >= seconds_per_message


def dispatch(recipient: str, message: str) -> None:
    """Sends `message` to `recipient` through every channel that's under its rate limit."""
    now = time.time()
    for channel_module, send_fn in _CHANNELS:
        if not _within_rate_limit(channel_module, now):
            continue
        send_fn(recipient, message)
        _last_sent_at[channel_module] = now
