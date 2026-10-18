# Rate limiter design

Each policy owns and validates its settings. The caller passes a configured
policy into `RateLimiter`, which handles locking and statistics.

```text
 SlidingWindowPolicy          TokenBucketPolicy          FuturePolicy
 -------------------          -----------------          ------------
 limit                        capacity                   its own settings
 window_ms                    refill_rate
         \                          |                          /
          \                         |                         /
           +------------------------+------------------------+
                                    |
                         all provide the same method:
                         check(client_id, endpoint)
                                    |
                                    | one configured policy is passed into
                                    v
                              RateLimiter
                         locking + statistics
                                    ^
                                    |
                                  Caller
```

For example:

```python
policy = SlidingWindowPolicy(limit=10, window_ms=1000)
limiter = RateLimiter(policy)
limiter.check(client_id="abc", endpoint="/users")
```

Both policies accept an optional, keyword-only `clock` callable at construction.
It returns nondecreasing integer milliseconds; the default uses
`time.monotonic_ns()`. Each policy stores its clock and reads it during `check()`.
Tests can control time without sleeping:

```python
now_ms = 0
policy = SlidingWindowPolicy(limit=1, window_ms=1000, clock=lambda: now_ms)
assert policy.check("abc", "/users").allowed
assert not policy.check("abc", "/users").allowed
now_ms = 1001
assert policy.check("abc", "/users").allowed
```

`TokenBucketPolicy(capacity=1, refill_rate=1, clock=lambda: now_ms)` accepts
the same clock argument.

Each request follows this path:

```text
Caller
  |
  | limiter.check(client_id, endpoint)
  v
RateLimiter
  |
  | acquires its lock
  | calls policy.check(client_id, endpoint)
  v
Configured policy
  |
  | uses its own settings and per-client/endpoint state
  | returns a Decision dataclass
  v
RateLimiter
  |
  | updates statistics and releases its lock
  | returns the decision
  v
Caller
```

A new policy inherits from `RateLimitPolicy` and implements its abstract
`active_keys` property and `check(client_id, endpoint)` method. Python prevents
instantiation of the base class or incomplete subclasses. Policies can introduce
their own constructor arguments; settings stay fixed for each limiter instance.

`stats()` reports the policy class name in `strategy`, along with
`total_allowed`, `total_rejected`, and `active_keys`. Each configured policy
owns mutable request state; use a separate policy instance for each limiter.

`check()` returns a `Decision` dataclass with `allowed`, `remaining`, and
`reset_after_ms` fields. Read the result through these named attributes.

## Relate to how this is a strategy pattern

```text
            RateLimiter              ← context
                 |
                 | holds a policy
                 v
          RateLimitPolicy            ← abstract strategy base class
          check(...) → Decision
                 ^
                 |
        +--------+---------+
        |                  |
SlidingWindowPolicy   TokenBucketPolicy
                      ↑
             concrete strategies
```

## Design BOW

**strategy pattern**, **composition**
Abstract Policy
Composition into RateLimiter rather than subclassing.
Sliding window -> key to request times
Token bucket -> key to (tokens, last_refill)
refill lazilly on request
handle fractional tokens to calc time
rem: clock drifts
lock at the rate limiter level
