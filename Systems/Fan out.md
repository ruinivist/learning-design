# Fan outs

very common as a re-usable block in larger systems.

what is basically describes is the **shape of data flow**, how that flow is actually
implemented ( usually event based and async ) can then be varied.

## An abstract fanout

```
                  ┌───────────────┐
                  │ Destination A │
                ┌▶│               │
                │ └───────────────┘
                │
┌──────────┐   ┌──────────────┐   ┌───────────────┐
│ Producer │──▶│   FAN-OUT    │──▶│ Destination B │
└──────────┘   │    BLOCK     │   └───────────────┘
               └──────────────┘
                │
                │ ┌───────────────┐
                └▶│ Destination C │
                  └───────────────┘
```

Internally based on architecture, you have these layers within that on "Fan Out Block"

- router => who gets this?
  - it's not like a one "thing" only, bazillion different types of messages are to be
    handled via the same fanout ( usually )
- distributor => multiplex to needed number of outputs ( virtually )
  - buffers/queues are usually used
- delivery
  - push/pull etc on consumers

### What do each of those mean?

**router**

A fanout NEEDS to understand the application, it's specific to the application as opposed
to something generic like a queue.

So for example, it NEEDS to understand that data entered is a "post" and then needs to
resolve it to the "follower" consumers.

```
PostCreated(user=Alice)
        │
        ▼
┌─────────────────────┐
│ Recipient Resolver  │
│                     │
│ followers(Alice)    │
└──────────┬──────────┘
           │
           ▼
 Bob, Jane, Sam, ...
```

This routing itself becomes problematic, what if we have millions of followers, usually
there is fan-out on fan-out ( batched in some manner ) for this celebrity problem.
But then again, that celebrity problem needs specific handling at every part of the system.

**distributor**
it's just a multiplexer, 1 event => N pieces of work

What you need to handle is slow consumer, crashed consumers, timeouts from them etc.

So this is tighly coupled with queues/buffers with different ack semantics.
```producer → queue → consumer` is to handle that "speed" diff and absord bt.

_some more components?_
backpressure needs to be reasoned about as well

**delivery**
which still needs to sit with fan-out as that is what handles the different sematics like
broadcast delivery vs competing consumers etc, AND also needs to understand ack semnatics
( again these layers kind of overlap, this is just a rough separation ).

## Implementation variations

| Strategy             | Fan-out happens                              | Main benefit            | Main cost                         |
| -------------------- | -------------------------------------------- | ----------------------- | --------------------------------- |
| Fan-out on write     | When data is created                         | Very fast reads         | Expensive writes                  |
| Fan-out on read      | When data is requested                       | Cheap writes            | Expensive reads                   |
| Push fan-out         | Producer sends downstream                    | Low latency             | Producer/distributor carries work |
| Pull fan-out         | Consumers retrieve work                      | Better consumer control | Possibly more latency             |
| Pub/Sub              | Broker replicates to subscribers             | Loose coupling          | Broker complexity                 |
| Scatter-gather       | Request sent to many nodes, results combined | Parallelism             | Need aggregation                  |
| Hierarchical fan-out | Fan-out happens in stages                    | Handles enormous N      | More architecture                 |
| Hybrid               | Different strategies for different cases     | Practical at scale      | More complexity                   |

**fan out on write**
primarily famous from social media feeds.

Idea being users read feeds significantly more than they publish, so you just _eagerly push_ for each follower.

Note that if that push is a unit of task, "celebrity problem" comes in. Frequent posters
who also have very huge number of followers, all of that SAME data is just pushed in feeds
of everyone.

**fan out on read**
it's the opposite here, lazy consumption => slower reads but writes become cheap ( overall )

**hybrid fan out**
this is what they do to handle the celebrity problem.
normal accounts -> fan out on write
massive accounts -> fan out on read ( so you do fetch the same content from them again but
it's likely cdn cached so we are good ). Basically a merge step would then handle the
pre-computed written feed and merge with celebrity posts.

---

This is another "dimension" instead of a new strategy; decided delivery semantics.

**Push**
the "fan-out" actively pushes to consumers but then you have problems with workers being
down that the fan out needs to handle.
This way, in case of a new event, it's immediately made known to consumer though, instead
of the consumer chekcing.

**Pull**

workers pull ( kafka style ) with ack ( usually twice, a taken and a done ).
this allows consumers to work on their pace.

---

I'll treat these as misc

**Pub/Sub**

almost a cannonical fan out model

publisher publishes to a "topic" and leaves it at that, it does not need to know anything
of the consumers.
consumers "sub"scribe to the topic to consume.

Delivery semantics are somewhat specific to this as well, these apply on publisher

| Semantic          | Guarantee                            | Consequence                                             |
| ----------------- | ------------------------------------ | ------------------------------------------------------- |
| **At-most-once**  | Message is delivered 0 or 1 times    | No duplicates, but messages can be lost                 |
| **At-least-once** | Message is delivered 1 or more times | No silent loss, but duplicates are possible             |
| **Exactly-once**  | Message is processed exactly once    | Strongest guarantee, but expensive/difficult end-to-end |

There's ack related variations on the consumption end as well, I'll treat pub-sub as
a separate topic to cover.

---

more misc

**scatter-gather**
fan-out + fan-in => basically parallel work loads that you scatter with a fan out and then
gather result to merge with a fan-out as well, 1 -> N -> 1.

**heirarchical fan-out**
this is just fan out that talks to another fan out; another celebrity problem solution
though worse than just read for the general social media setting. I guess it would make
sense if SOME batched compute is needed to be done eagerly.
