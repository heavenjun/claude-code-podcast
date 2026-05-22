"""Shared utilities: retry wrapper for transient Gemini API errors."""

import time
from google.genai import errors as genai_errors


def call_with_retry(fn, *args, max_retries: int = 6, base_wait: int = 30, **kwargs):
    """Call fn(*args, **kwargs), retrying on 503 with exponential backoff.

    Waits: 30s, 60s, 120s, 240s, 480s (total up to ~15 min before giving up).
    """
    for attempt in range(max_retries):
        try:
            return fn(*args, **kwargs)
        except genai_errors.ServerError as exc:
            status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
            if status == 503 and attempt < max_retries - 1:
                wait = base_wait * (2 ** attempt)
                print(
                    f"  [503 UNAVAILABLE] Attempt {attempt + 1}/{max_retries}. "
                    f"Retrying in {wait}s… ({exc})"
                )
                time.sleep(wait)
            else:
                raise
