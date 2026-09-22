import hmac
import secrets
import threading
import time
from collections import defaultdict, deque

from flask import abort, request, session

_CSRF_KEY = "_csrf_token"


def csrf_token():
    """Return this session's CSRF token, creating it on first use."""
    token = session.get(_CSRF_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        session[_CSRF_KEY] = token
    return token


def check_csrf(token=None):
    """Abort with 400 unless the submitted token matches the session token.

    Reads from the posted form by default. Pass `token` explicitly for
    non-form requests (e.g. a JSON body).
    """
    sent = token if token is not None else request.form.get("csrf_token", "")
    expected = session.get(_CSRF_KEY, "")
    if not expected or not hmac.compare_digest(sent.encode(), expected.encode()):
        abort(400)


class RateLimiter:
    """Small in-memory sliding-window limiter (per server process)."""

    def __init__(self):
        self._hits = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key, limit, window_seconds):
        now = time.monotonic()
        with self._lock:
            if len(self._hits) > 5000:  # keep memory bounded
                stale = [k for k, q in self._hits.items()
                         if not q or now - q[-1] > window_seconds]
                for k in stale:
                    del self._hits[k]
            q = self._hits[key]
            while q and now - q[0] > window_seconds:
                q.popleft()
            if len(q) >= limit:
                return False
            q.append(now)
            return True


limiter = RateLimiter()
