"""Transient-error retry decorator — Gold tier error-recovery utility.

Matches the `with_retry` pattern from the hackathon spec § 7.2. Use it
on any function that calls an external API where transient network
errors or rate-limit bumps are expected. Do NOT use it on user-facing
operations (drafting, approval moves) — those should surface errors
immediately so the human can decide.

Example:
    from orchestrator.retry import with_retry, TransientError

    @with_retry(max_attempts=3, base_delay=1, max_delay=30)
    def fetch_gmail_message(msg_id: str) -> dict:
        return gmail_service.users().messages().get(id=msg_id).execute()
"""
from __future__ import annotations

import functools
import logging
import random
import time
from typing import Callable, TypeVar

log = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., object])


class TransientError(Exception):
    """Raise to signal a retryable failure (network blip, 429, 503).

    Non-transient errors (auth failures, 4xx client errors other than 429)
    should raise their own exception types and will NOT be retried.
    """


# Exceptions we automatically treat as transient even when raised
# without wrapping. Keep the list narrow; false positives cause retries
# on bugs.
_AUTO_TRANSIENT = (
    ConnectionError,
    TimeoutError,
)


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True,
) -> Callable[[F], F]:
    """Exponential-backoff retry decorator with jitter.

    Args:
      max_attempts: total tries including the first. 1 = no retry.
      base_delay:   seconds before first retry. Doubles each attempt.
      max_delay:    ceiling. Even large backoffs never exceed this.
      jitter:       add 0–25% random jitter to each sleep so N callers
                    don't thundering-herd the same API.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):  # type: ignore[no-untyped-def]
            last_exc: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except TransientError as e:
                    last_exc = e
                except _AUTO_TRANSIENT as e:
                    last_exc = e
                except Exception:
                    # Non-retryable. Bubble up immediately.
                    raise

                if attempt == max_attempts:
                    break
                delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
                if jitter:
                    delay += random.uniform(0, delay * 0.25)
                log.warning(
                    "retry.backoff",
                    extra={
                        "func": func.__name__,
                        "attempt": attempt,
                        "max_attempts": max_attempts,
                        "delay_seconds": round(delay, 2),
                    },
                )
                time.sleep(delay)
            assert last_exc is not None
            raise last_exc  # noqa: B904 — intentional re-raise after loop

        return wrapper  # type: ignore[return-value]

    return decorator
