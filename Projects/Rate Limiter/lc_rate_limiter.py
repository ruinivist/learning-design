import time
import math
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class RateLimitPolicy(ABC):
    @abstractmethod
    def check(
        self, key, *, limit=None, window_ms=None, capacity=None, refill_rate=None
    ) -> tuple[bool, int, int]: ...

    @property
    @abstractmethod
    def active_keys(self) -> int: ...


@dataclass(slots=True)
class SlidingWindowState:
    request_times: list[int] = field(default_factory=list)


@dataclass(slots=True)
class TokenBucketState:
    tokens: float
    last_refill_ms: int


class SlidingWindowPolicy(RateLimitPolicy):
    def __init__(self):
        self.state: dict[tuple[str, str], SlidingWindowState] = {}

    @property
    def active_keys(self):
        return len(self.state)

    def check(
        self, key, *, limit=None, window_ms=None, capacity=None, refill_rate=None
    ):
        if limit is None or window_ms is None:
            raise ValueError("Sliding window requires limit and window_ms")

        now = time.monotonic_ns() // 1_000_000
        times = self.state.setdefault(key, SlidingWindowState()).request_times

        times[:] = [t for t in times if t > now - window_ms]

        if len(times) < limit:
            times.append(now)
            return True, limit - len(times), 0

        return False, 0, times[0] + window_ms - now


class TokenBucketPolicy(RateLimitPolicy):
    def __init__(self):
        self.state: dict[tuple[str, str], TokenBucketState] = {}

    @property
    def active_keys(self):
        return len(self.state)

    def check(
        self, key, *, limit=None, window_ms=None, capacity=None, refill_rate=None
    ):
        if capacity is None or refill_rate is None:
            raise ValueError("Token bucket requires capacity and refill_rate")

        now = time.monotonic_ns() // 1_000_000
        state = self.state.setdefault(key, TokenBucketState(capacity, now))

        state.tokens = min(
            capacity, state.tokens + (now - state.last_refill_ms) * refill_rate / 1000
        )
        state.last_refill_ms = now

        if state.tokens >= 1:
            state.tokens -= 1
            result = True, int(state.tokens), 0
        else:
            wait = math.ceil((1 - state.tokens) * 1000 / refill_rate)
            result = False, 0, wait

        return result


class RateLimiter:
    def __init__(self, strategy="policy_a"):
        if strategy not in ("policy_a", "policy_b"):
            raise ValueError("Unknown strategy")

        self.strategy = strategy
        self._policy = (
            SlidingWindowPolicy() if strategy == "policy_a" else TokenBucketPolicy()
        )

        self._lock = threading.Lock()
        self._allowed = 0
        self._rejected = 0

    def check(self, client_id, endpoint, limit, window_ms, capacity, refill_rate):

        with self._lock:
            key = (client_id, endpoint)

            result = self._policy.check(
                key,
                limit=limit,
                window_ms=window_ms,
                capacity=capacity,
                refill_rate=refill_rate,
            )

            if result[0]:
                self._allowed += 1
            else:
                self._rejected += 1

            return result

    def stats(self):
        with self._lock:
            return {
                "strategy": self.strategy,
                "total_allowed": self._allowed,
                "total_rejected": self._rejected,
                "active_keys": self._policy.active_keys,
            }
