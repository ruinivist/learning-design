# lru

## avoid

inheritance hell, cons can be
- no runtime swap
- policy you can test isolated
- with just policy there's one axis of variation, but say u add another like a backend, types explode geometrically rather than compositions where it'll be just an arg

## high level idea


```
                ┌──────────────────────────────┐
   client ────▶ │ Cache[K, V]                   │
                │ - capacity                   │
                │ - storage: key → value       │
                │ - on_evict callback (opt.)    │
                │ - policy ────────────────────┼──┐
                └──────────────────────────────┘  │ has-a (composition)
                                                  ▼
                              ┌──────────────────────────────┐
                              │ EvictionPolicy[K] (abstract) │
                              │ on_insert(key)               │
                              │ on_access(key)               │
                              │ evict() → key                │
                              └──────────────┬───────────────┘
                                   ┌─────────┴─────────┐
                                   ▼                   ▼
                          ┌────────────────┐  ┌────────────────┐
                          │ LRUPolicy[K]   │  │ FIFOPolicy[K]  │
                          │ order: recency │  │ order: arrival │
                          │ access → move  │  │ access → no-op │
                          │ to most recent │  │                │
                          └────────────────┘  └────────────────┘
```

## followups

TTL: time to live?
in this case eviction happens before capacity so you need a way to signal the policy
that the cache is going to evict something OUT of policy just because of TTL
in this case you would need an `on_evict(key)` to signal the policy to update it's internals

Thread safety?
A trivial way is to lock at the cache level, but then we have eliminated race condition sby eliminating
concurrency.
Another approach is sharding, so we split keys into shards and have effectively N independent caches.
In this case, only approx order can work
Buffered policy updated ( java's caffeine lib ), you let reads directly hit the concurrent hash map ( store ),
for python I would need to lock anyways but just for store not policy, policy updated are to be applied as a
batch, policy application thne is slighly stale as a tradeoff.
