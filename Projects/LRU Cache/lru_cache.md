# LRU cache design

`Cache` owns capacity and stored values. An injected `EvictionPolicy` tracks keys
and chooses which one to remove; LRU, LFU, and FIFO provide different rules.

![LRU cache UML class diagram](lru-cache-uml.svg)

## Reading the UML

1. **Start with `Cache`:** `get()` and `put()` keep values and policy metadata in sync.
2. **Follow `EvictionPolicy`:** Strategy separates eviction rules from storage. Each policy handles access, insertion, and victim selection.
3. **LRU data:** A key-to-`Node` map finds entries; `DLList` moves accessed nodes to the front and evicts from the back.
4. **Other policy data:** LFU tracks frequencies and their key sets; FIFO keeps insertion order in a deque. Neither stores values.

## Happy path

1. Create `Cache(2, LRU())`; `put("A", 1)` and `put("B", 2)` store values and register their keys with LRU.
2. `get("A")` calls `on_access("A")`, moving A's node to the front, then returns `1`.
3. `put("C", 3)` finds the cache full and calls `policy.evict()`.
4. LRU removes B from the list and its node map, then returns `"B"`.
5. The cache deletes B's value, stores C, and calls `on_insert("C")`.
6. `get("C")` promotes C and returns `3`; A and C remain cached.

## Design BOW

- **Composition:** Choose a policy when constructing the cache; keep values separate from eviction metadata.
- **LRU:** Dictionary lookup plus a circular sentinel list gives constant-time lookup, promotion, and eviction. Nodes compare by identity.
- **LFU:** Frequency buckets and `min_freq` find a least-used key; ties are arbitrary, not LRU.
- **FIFO:** Reads do not change insertion order. Existing-key writes count as accesses for LRU and LFU.
- **Extensions:** TTL needs a policy hook for arbitrary removal. LRU is vulnerable to scans; a probation/protected split such as SLRU can reduce pollution.

## GoF patterns

| Pattern | Where | Purpose |
| --- | --- | --- |
| **Strategy** | `Cache` receives an `EvictionPolicy`; `LRU`, `LFU`, and `FIFO` implement it. | Change eviction rules without changing storage operations. |

## SOLID principles

| Principle | Where / how |
| --- | --- |
| **Single Responsibility** | Cache manages values and capacity; policies manage eviction order. |
| **Open/Closed** | Add a policy without changing `Cache.get()` or `put()`. |
| **Dependency Inversion** | Cache depends on the abstract policy contract; callers choose its implementation. |

## Concurrency

| Concern | Implementation |
| --- | --- |
| **Shared access** | No locks exist. Concurrent calls can desynchronize storage and policy metadata. |
| **Read mutations** | Hits update policy state as well as writes; neither operation is synchronized. |
| **Policy ownership** | Give each cache a fresh policy; sharing or swapping populated policies breaks their correspondence with storage. |

## common mistakes

- Keep policy updates and value changes together; eviction removes the key from both.
- LFU assumes eviction is followed by insertion to reset `min_freq`; it does not support arbitrary standalone removals.
- LFU retains empty frequency buckets, so metadata can grow with repeated hits.
- `get()` returns `None` for both a missing key and a stored `None` value.
