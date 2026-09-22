"""Minimal, privacy-respecting event counter.

No cookies, no IP storage, no per-visitor identifiers. Each call increments
a counter for one of a fixed set of named events. That's it.
"""
import logging
import threading
from collections import Counter

log = logging.getLogger("analytics")

ALLOWED_EVENTS = {
    "project_page_viewed",
    "service_viewed",
    "contact_button_clicked",
    "project_form_started",
    "project_form_submitted",
}

_lock = threading.Lock()
_counts = Counter()


def record(event, label=""):
    if event not in ALLOWED_EVENTS:
        return False
    label = (label or "")[:60]
    with _lock:
        _counts[event] += 1
    log.info("event=%s label=%s", event, label)
    return True


def snapshot():
    with _lock:
        return dict(_counts)
