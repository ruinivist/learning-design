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

A new policy can introduce its own constructor arguments while keeping the
same `check(client_id, endpoint)` interface. Policy settings stay fixed for
each limiter instance.

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
          RateLimitPolicy            ← strategy interface
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
