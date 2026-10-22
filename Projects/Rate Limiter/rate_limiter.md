# Rate limiter design

`RateLimiter` owns locking and statistics and delegates decisions to a configured `RateLimitPolicy`. Each policy owns its settings, clock, and state per `(client_id, endpoint)`.

These notes cover [rate_limiter.py](rate_limiter.py); `lc_rate_limiter.py` is a separate variant with per-call settings and a different sliding-window boundary. For incremental recall, use the [breakdown](rate-limiter-breakdown.md).

![Rate limiter UML class diagram](rate-limiter-uml.svg)

## Reading the UML

1. Start with `RateLimiter`. It holds one policy, a `threading.Lock`, and allowed/rejected counters. Callers use `check()` for admission and `stats()` for a snapshot.
2. Follow `RateLimitPolicy` to its implementations. The contract requires `check(client_id, endpoint)` and the read-only `active_keys` property. The limiter delegates the algorithm while keeping synchronization and statistics in one place.
3. Follow each policy to the state it owns. `SlidingWindowPolicy` maps keys to `SlidingWindowState.request_times`; `TokenBucketPolicy` maps keys to `TokenBucketState.tokens` and `last_refill_ms`. Keys separate both clients and endpoints.
4. Settings and the clock belong to each policy. Constructors validate settings; the injected clock supplies integer milliseconds. State is created when a key is first checked.
5. Follow `Decision` back to the caller. `allowed` reports admission, `remaining` reports whole requests available immediately after the check, and `reset_after_ms` reports a retry delay on rejection. Accepted decisions use zero delay. The limiter counts the result before returning it.

## Happy path

1. Construct `SlidingWindowPolicy(limit=2, window_ms=1000)` and pass it to `RateLimiter`.
2. Call `limiter.check("alice", "/users")`. The limiter acquires its lock and calls the policy with those arguments.
3. The policy creates an empty state for `("alice", "/users")` and reads its clock. Assume it returns `5000`.
4. The cutoff is `4000`. There are no expired timestamps to remove, and the list contains fewer than two entries, so the policy appends `5000`.
5. The policy returns `Decision(allowed=True, remaining=1, reset_after_ms=0)`.
6. The limiter increments `_total_allowed`, releases the lock, and returns that decision. A subsequent `stats()` call under the same lock reports one allowed request, zero rejections, and one tracked key.

## Design choices

- Inject one configured policy into the limiter. Its settings apply independently to every key; the API has no per-key settings or policy-switching method.
- Sliding window records accepted requests only. `bisect_left()` finds the first timestamp at least `now - window_ms`; deleting the prefix retains the inclusive interval `[now - window_ms, now]`. Rejection does not append a timestamp.
- A full window returns `oldest + window_ms - now` as its delay. At the exact boundary this can be zero while the request is still rejected: the oldest timestamp expires only after the boundary. A caller retrying at the same clock value can be rejected again.
- Binary search locates the expired prefix in logarithmic time, but deleting it from a Python list can move entries in linear time. Each key retains at most `limit` timestamps.
- Token bucket starts each new key at `capacity`. On later checks it adds `elapsed_ms / 1000 * refill_rate` tokens, capped at capacity. `refill_rate` is tokens per second; refill happens on requests without a background thread.
- An accepted bucket check consumes one token and reports `floor(tokens)` remaining. Rejection preserves the fractional balance and returns `ceil((1 - tokens) / refill_rate * 1000)`. This is time until one token, not until the bucket is full.
- Both policies require a nondecreasing clock in integer milliseconds; the default uses `time.monotonic_ns() // 1_000_000`. Pass `clock=lambda: now_ms` to control time without sleeping. The bucket ignores nonpositive elapsed time; the sliding window relies on sorted timestamps.
- Constructors reject nonpositive limits, windows, and capacities, plus nonpositive or nonfinite refill rates. Policy exceptions propagate through `check()` without incrementing either counter; the context manager releases the lock.
- `stats()` returns a fresh dictionary containing the policy class name, allowed/rejected totals, and `active_keys`. That count includes idle keys because neither policy evicts entries. State lives in memory and is lost when the process exits.

## Design patterns

| Pattern | Where | Purpose |
| --- | --- | --- |
| Strategy | `RateLimiter` holds a `RateLimitPolicy`; sliding window and token bucket inherit it. | Choose an algorithm at construction without changing locking, statistics, or callers. |

## Design principles

| Principle | Where / how |
| --- | --- |
| Single responsibility | Policies handle rate-limit decisions and state; the limiter handles synchronization and statistics. |
| Open/closed | Add a policy implementing `check()` and `active_keys` without changing `RateLimiter`. |
| Dependency inversion | `RateLimiter` accepts the abstract policy contract; the caller selects the concrete implementation. |

## Concurrency

| Concern | Implementation |
| --- | --- |
| Over-admission | One limiter lock covers policy lookup, clock reads, expiration/refill, admission, state changes, and counter updates. |
| Consistent statistics | `stats()` uses the same lock, so it cannot observe a completed policy check before its counter update. |
| State ownership | Use a separate policy instance per limiter and access it through that limiter. Direct policy calls have no locking; sharing a policy between limiters puts its state behind different locks. |
| Reentrant calls | `threading.Lock` is not reentrant. A custom policy or clock must not call back into the same limiter's `check()` or `stats()` while it holds the lock. |
| Tradeoff | All keys serialize through one limiter lock. Separate limiter instances and separate processes do not share quotas or statistics. |

## Common mistakes

- Lock the whole decision/update operation; policies are not independently synchronized.
- Key by both client and endpoint; client-only keys mix unrelated quotas.
- Keep time monotonic and units consistent; refill rates are tokens per second.
- Retain fractional tokens; ceil the wait for the missing fraction.
- Check sliding-window boundaries: this implementation retains timestamps exactly at the cutoff, even when the reported wait reaches zero.
- `active_keys` counts tracked keys, not recent activity; idle entries are never evicted.
