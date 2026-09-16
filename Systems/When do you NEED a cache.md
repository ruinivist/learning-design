# When do you need a cache?

So it seems like every book/online that tries to teach system design ( the ones I have
seen so far atleast ) REALLY like to glue ( DB + Cache ) every single time unless you want
0 stale reads, now my question here is, if it really was so ubiquitous, shouldn't DBs do
it or have an option to enable it in some way?

## Don't DBs anyways have a cache?

I mean isn't 99% of software optimisation just batching and caching.
There's OS level caches, db level caches, do you REALLY need a redis cache sitting on
top as well?

There's several cases to consider here, all come with implicit assumption.

1. Put a DB on the HOST itself.

This way you need 0 network traversals for getting to db so no auth on the hot path.
You can even use something like "RocksDB" which is very optimised for throughput by using
as much memory as it can, with a persistent layer to it as well.

BUT

- you NEED to put all application data, else if it's sharded you are REALLY making a
  specific structure. Putting all application data on each host is just not viable.
- replication, you will have to settle for eventual consistency which is fine given
  you were anyways using a cache.
- it keeps application then ephemereal which can help with availaibility but then ofc you
  are shifting that availability load to DB ( assumtion here is to KEEP db concentrated
  and separate now that it owns the single point of failure )

It can work great for monoliths but the biggest problem ofc is the large amount of data.
If you NOT using a monolith then it's pretty much implied that it's too much data for a
single machine.

### But what if I can REALLY make it sharded?

It's a specific architecture then, we assume for most cases the application would just
read from it's own shard. Replication we can assume per shard to have eventual consistency
with replicas. In fact something like, LB => application I ( three replicated DB and apps )

BUT then LB cannot route to arbitrary shard, you do need it to go to the same shard.

### The compromise

I feel like to move the hardest of challenges => maximising DB uptime, having db separate
and ephemereal application code ( in which an application layer cache does make sense )
has been practically useful, especially with all vendors supporting it ( backwards logic )
but also allowing for the MORE error prone code ( application ) to just be recycled and
restarted AS fast as possible ( especially with containers ) and then focus on DB where the
contract is limited but you NEED more guarantees.
