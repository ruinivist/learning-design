# Design twitter

## What are we actually making?

Twitter has

- tweets = text of 140 chars ( need to handle "runes" )
- follows = a user "relation" graph
- timelines aka feeds
  - recommender enginer
- likes, replies ( attached to tweets )
- ads
- moderation
- search
- notification
- media store
- analytics for trends

**Scope management**
let's consider only the very core features, the way to go about it is => what can I remove
and it'll still remain twitter

- 140 chars messages
- follows
- timelines

## Functional requirements ( FRs )

Users can

- tweet
  - needs CRUD + media
- follow, unfollow
- like, reply
- view other tweets
- my timeline

## Non-functional requirements ( NFRs )

try to map product semantics to infrastructural semantics

- tweet
  - write/update => durable, eventually done
  - read => low latency, stale is somewhat fine

- home timeline
  - low latency, relevant ( recommender service ) = pre-computed

- follow, like
  - no latency requirements BUT eventually consistent

## Scale estimation

```
DAU = ~250 mil

Tweets/Day = ~500mil ( some users don't so majority will take it )
    - tweets / sec = > ~6k tweets / sec
    - to handle peaks, assume peak multipliers is 10 = ~60k tweets / sec

Timeline requests = assume 20 per active user => 5 billion
    - 5 bil / (24 * 60 * 60) => ~60k timeline req / sec
    - at peak ( 10x ) => 600k req/sec

Per timeline tweets
    - assume each timeline sends 30 items
    - ~1.8 mil tweets fetch / sec
    - at peak => 18 mil per sec

Writes per users = 2 ( we ssumed 2, to get to tweets per day )
Reads per users = 20 ( feed ) * 30 ( in each ) = 600
=> reads dwarf writes

Twitter specific obervation
- follower graph and poster skew

Same people are followed by most, and those same ones post a lot as well.
If you do not handle them separately, a single tweet can trigger millions of downstream
ops
```

## Data model

let's ignore runes handling for now

Look at an ideal state, 3NF / BCNF and then optimise for reads at the cost of more data /
nulls

```
User
---
id PK
metadata ... don't care at this stage

Tweet
---
tweet_id PK
author_id FK
text
created_at
reply_to
quoted_tweet_id

> fixed cardinality relations commonly needed when hydrating a tweet should be inline
> especially for read heavy cases => here reply_to and quoted_tweet_id
===

TweetMedia
---
tweet_id FK
media_id FK
position
(tweet_id, media_id) PK

===
Media
---
media_id PK
type
storage_key ( in object store )
created_at

=== DERIVED DATA

Following ( directed edges graph )
---
follower_id
followee_id
created_at
(follower_id, followee_id) PK

=== EVENT DATA

TimelineEntry ( this is persisted as well )
---
user_id
tweet_id
inserted_at ( better name that clearly conveys entry insertion as created at can meean
tweet creation time as well )

===

TweetImpression
---
in future perhaps, let's leave for now
```

> created_at is a bit subjective, for "entities" you def need it, for some relations as well
> where those relations can be used in downstream tasks / analytics

For example created_at on a TweetMedia obviously makes 0 sense.

## APIs

using rest verbs ( well somewhat )

```
POST /tweets
GET /tweets/{tweet_id}

POST /users/{id}/follow
DELETE /users/{id}/follow

// scrolling some else's post
GET /users/{id}/timeline?cursor=...

// my curated homepage
GET /timeline/home?cursor=...
```

Nice idea => post on /tweets should have an idempotency key that clients manage and send.
Client have perfect info on the actual user interaction to detect actual duplicate posts vs
network based retries. This way clients can retry freely without worrying about double posts
being created.

## Architecture

![Twitter architecture](./Twitter%20architecture%20diagram.png)

The image is not perfect and misses some edges but it roughly does the job.
Some issues

- tweet service to outbox is just not there
- no outgoing edges from home timeline store / author timeline store

## The hybrid fanout

For making the timeline, the fanout is split into two, push on read and push
on write => hybrid. What does each side buy us?

What does a timeline look like?
Look at all my followers, get theirs recent posts, rank them by time is the
simplest model, but traversing followers and their posts as well right during
a timeline request would make it very slow, so it makes sense to pre-compute
that for each user. This can crudely be a mapping from user to an array of the
tweet ids they are meant to see.
The even that triggers this eager compute for ME is when someone I follow posts.
( obviously it would be somer sort of merge instead of a full compute over all
my followers as I've outline above )

But when a celebrity posts, this triggers that merge step for millions of people.
I also don't wanna be duplicating that same few ids millions of times.
The hybrid approch is just doing that on demand compute as I outlined but just
over a smaller set.

So it splits as, get my pre-computed list ( read so fast ) + get my celebrity
followers and get their tweets. This second step can just be a db hit but usually
even for celeb if there's some pre-processing needed then it is stored via
the celeb fanout into a author timeline store ( could be something as simple as
a queue of top N recent so I don't have to do a db read to filer by time ).

## Failure semantics

We divide the product into three parts now

- core systems
  - losing these threaten correctness and durability
  - canonical tweet db
- derived systems
  - fine if they get stale for some time or are lost as we can
    rebuilt them
  - hometimeline stores
- optional systems
  - analytics

Another image but the core terms to look for and cover are

- circuit breakers around optional stuff
- backpressure to have bounded oncurrency
- critical write path must be synchornous and succeed before ack
- graceful degradation => fallbacks kick in automatically instead. This is
  done by having the optional services "consume" failures within them.

![Twitter failure semantics](./Twitter%20failure%20semantics.png)

## Infra choices

What commercial / open source services do we use in the end?

### when do you use something like Cassandra\_?

It has nothing to do iwth distributed or not as postgres can be distributed
as well. You use thne you want "wide-column", high write througput writes.
It's easier with an example.

```
user_42 partition

inserted_at       tweet_id
--------------------------
10:05:03          991
10:04:51          982
10:03:17          970
```

In cassandra, you can define the model as

```
partition key = user_id
clustering key = inserted_at
```

So this gives you key -> modify the value smartly, not just as a whole like
a kv store. Note that this is a NoSQL db, but not quite a KV.
The term is "wide-column" => one partition key can have a very large ("wide")
number of values associated with the key ( here tweet_ids ); not this is not
what's expected for a kv.

What you do lose is some of transaction guarantees ( it has some but ofc it's
not SQL ) and complex joins/cross table queries.

### so back to our infra choices?

| Component                 | Choice                     | Why                                                                                                               |
| ------------------------- | -------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| **Tweet Store**           | **Distributed PostgreSQL** | Canonical data; we want durable writes and a real transaction for `Tweet + Outbox`.                               |
| **Follow Graph Store**    | **Distributed PostgreSQL** | Canonical relationship data; simple indexed access in both directions, plus clean uniqueness/constraint handling. |
| **Home Timeline Store**   | **Cassandra**              | Derived, append-heavy, enormous write throughput; natural `user_id → ordered tweet_ids` partition model.          |
| **Author Timeline Store** | **Cassandra**              | Same access pattern, keyed by `author_id`; recent ordered tweets with high write/read throughput.                 |
| **Event Log**             | **Kafka**                  | Durable, replayable event stream with partitioning and independent consumer groups.                               |
| **Fanout Work Queue**     | **Kafka**                  | Reuse the streaming infrastructure; planner emits bounded fanout chunks that workers consume independently.       |
| **Media Storage**         | **S3**                     | Durable object storage for images/video; DB stores only metadata and object keys.                                 |
| **Search**                | **Elasticsearch**          | Dedicated inverted index for full-text tweet search.                                                              |
| **Cache, if needed**      | **Redis**                  | Only introduce it for hot-object shielding or expensive hydration—not by default.                                 |

Notes

- for follow graph store, can also use some graph database like Neo4j or Neptune as deep hop relationships while
  not useful for the application, would be very much needed for recommender systems.
