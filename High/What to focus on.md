# What to focus on?

- A good link: https://www.hellointerview.com/learn/system-design/in-a-hurry/delivery

A quick checklist to not be lost.

## 1. Scope · 5 min

- **Core actions:** what can you remove and still have the product? Twitter: post, follow, read feed.
- **Guarantees per action:** latency target, acceptable staleness, data that cannot be lost. Feed may lag; acknowledged posts must survive.
- **Exclude explicitly:** search, ads, recommendations. Confirm scope.

## 2. Scale · 3 min

- **Peak requests/sec:** daily actions ÷ 86,400 × peak multiplier. Separate reads and writes.
- **Storage:** writes/sec × bytes/write × retention seconds. Include replicas if sizing hardware.
- **Skew and amplification:** busiest key/user; downstream operations per request. One celebrity post → millions of feed updates.
- **Consequence:** name the design choice each estimate changes.

## 3. APIs and data · 7 min

- **Endpoints:** inputs, outputs, authorization, pagination. Example: `GET /feed?cursor=…`.
- **Queries → schema → store:** keys, indexes, ordering; updates that need one transaction.
- **Source of truth:** posts/follows are durable; feeds are derived and rebuildable.
- **Write contract:** what commits before success? Client retry after a lost response must not create duplicates.

## 4. Architecture · 10 min

- **Trace a write:** client → service → database → acknowledgment. Mark asynchronous work.
- **Trace a read:** client → service → lookup/query → response. Include pagination.
- **Justify additions:** cache for which expensive read? Queue for which deferred work? Shard on which key?
- **Choose technology:** match access patterns and guarantees; name the compromise.

## 5. Deep dive · 15 min

- **Pick the hardest requirement:** interviewer’s choice, or your biggest correctness/scale risk.
- **Hot key:** how does a celebrity change the read/write strategy?
- **Partial failure:** database commits, event publish fails. How does downstream work eventually happen?
- **Retries:** duplicate/out-of-order events; how are updates made safe?
- **Overload:** bounded queues, admission limits, backpressure; what gets rejected or delayed?
- **Recovery:** dependency down or derived store lost; fallback, rebuild, catch up with ongoing writes.
- **Cost:** state what your fix sacrifices: latency, freshness, storage, or operating complexity.

## 6. Close · 5 min

- **10× traffic:** first bottleneck → metric that exposes it → next change.
- **Recap:** guarantees met, compromises accepted, biggest unresolved assumption.
- **Behind schedule:** cut secondary endpoints and arithmetic. Keep one request trace and one deep dive.
