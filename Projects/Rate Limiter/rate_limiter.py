from __future__ import annotations

from dataclasses import dataclass, field
import bisect
import math
import threading
import time
from typing import Protocol, TypedDict, Tuple

# (client id, endpoint)
RateLimitKey = Tuple[str, str]


@dataclass(slots=True)
class Decision:
    allowed: bool
    remaining: int
    reset_after_ms: int


class StatsDict(TypedDict):
    strategy: str
    total_allowed: int
    total_rejected: int
    active_keys: int


# ---------------------------------------------------------------------------
# Policy interface
# ---------------------------------------------------------------------------


class RateLimitPolicy(Protocol):
    @property
    def active_keys(self) -> int: ...

    def check(
        self,
        client_id: str,
        endpoint: str,
    ) -> Decision: ...


# ---------------------------------------------------------------------------
# Policy A: Sliding Window
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class SlidingWindowState:
    request_times: list[int] = field(default_factory=list)


class SlidingWindowPolicy:
    def __init__(self, limit: int, window_ms: int) -> None:
        if limit <= 0:
            raise ValueError("limit must be > 0")
        if window_ms <= 0:
            raise ValueError("window_ms must be > 0")

        self._limit = limit
        self._window_ms = window_ms
        self._state: dict[RateLimitKey, SlidingWindowState] = {}

    @property
    def active_keys(self) -> int:
        return len(self._state)

    def check(
        self,
        client_id: str,
        endpoint: str,
    ) -> Decision:
        key = (client_id, endpoint)

        state = self._state.setdefault(
            key,
            SlidingWindowState(),
        )

        now = _now_ms()
        cutoff = now - self._window_ms

        # Timestamps are sorted; discard only those older than the window.
        # we keep >= cutoff
        first_valid = bisect.bisect_left(
            state.request_times,
            cutoff,
        )

        if first_valid:
            # clear the prefix on that
            del state.request_times[:first_valid]

        if len(state.request_times) < self._limit:
            state.request_times.append(now)

            remaining = self._limit - len(state.request_times)

            return Decision(allowed=True, remaining=remaining, reset_after_ms=0)

        reset_after_ms = state.request_times[0] + self._window_ms - now

        return Decision(allowed=False, remaining=0, reset_after_ms=reset_after_ms)


# ---------------------------------------------------------------------------
# Policy B: Token Bucket
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class TokenBucketState:
    tokens: float
    last_refill_ms: int


class TokenBucketPolicy:
    def __init__(self, capacity: int, refill_rate: float) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be > 0")
        if refill_rate <= 0 or not math.isfinite(refill_rate):
            raise ValueError("refill_rate must be finite and > 0")

        self._capacity = capacity
        self._refill_rate = refill_rate
        self._state: dict[RateLimitKey, TokenBucketState] = {}

    @property
    def active_keys(self) -> int:
        return len(self._state)

    def check(
        self,
        client_id: str,
        endpoint: str,
    ) -> Decision:
        key = (client_id, endpoint)
        now = _now_ms()

        state = self._state.get(key)

        if state is None:
            state = TokenBucketState(
                tokens=float(self._capacity),
                last_refill_ms=now,
            )
            self._state[key] = state
        else:
            elapsed_ms = now - state.last_refill_ms

            # guarding against clock drifts
            if elapsed_ms > 0:
                elapsed_seconds = elapsed_ms / 1000

                # Refill lazily on each request, capped at the burst capacity.
                state.tokens = min(
                    float(self._capacity),
                    state.tokens + elapsed_seconds * self._refill_rate,
                )

                state.last_refill_ms = now

        if state.tokens >= 1:
            state.tokens -= 1

            return Decision(
                allowed=True,
                remaining=math.floor(state.tokens),
                reset_after_ms=0,
            )

        # rem that this can be partial, like 0.4, so we calc how long to get 0.6
        # tokens and ceil that
        fraction_missing = 1 - state.tokens

        reset_after_ms = math.ceil(fraction_missing / self._refill_rate * 1000)

        return Decision(allowed=False, remaining=0, reset_after_ms=reset_after_ms)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class RateLimiter:
    """Apply a configured policy with locking and request statistics.

    Example:
        limiter = RateLimiter(SlidingWindowPolicy(limit=10, window_ms=1000))
        limiter.check(client_id="abc", endpoint="/users")
    """

    def __init__(self, policy: RateLimitPolicy) -> None:
        self._policy = policy

        self._lock = threading.Lock()

        self._total_allowed = 0
        self._total_rejected = 0

    def check(
        self,
        client_id: str,
        endpoint: str,
    ) -> Decision:
        """Return a Decision for this request."""

        # Keep the policy's state changes and statistics in one critical section.
        with self._lock:
            result = self._policy.check(
                client_id=client_id,
                endpoint=endpoint,
            )

            if result.allowed:
                self._total_allowed += 1
            else:
                self._total_rejected += 1

            return result

    def stats(self) -> StatsDict:
        with self._lock:
            return {
                "strategy": type(self._policy).__name__,
                "total_allowed": self._total_allowed,
                "total_rejected": self._total_rejected,
                "active_keys": self._policy.active_keys,
            }


def _now_ms() -> int:
    # a mono clock does not go back
    return time.monotonic_ns() // 1_000_000
