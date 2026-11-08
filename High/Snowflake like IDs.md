# Snowflake IDs

## The problem

Generate GLOBALLY unique ids, loosely time ordered ascending, in a distributed manner
across MANY machines without any communication

What it gives me?

- each server / machine can generate ids locally with 0 communication/sync overhead

Just a timestamp won't do as then it can't be GUARANTEED globally unique, we need to
determine a time based prefix ( for the loose time ordering ) and a machine level suffix
that still makes it globally unique.

- all in 64 bits for standardised storage, the main challeneg then is how to partition
  those 64 bits

## Snowflake IDs

```
 63                                                        0
 ┌─┬─────────────────────────┬──────────┬────────┬────────────┐
 │0│      timestamp          │data ctr  │ worker │ sequence   │
 └─┴─────────────────────────┴──────────┴────────┴────────────┘
  1          41 bits            5 bits    5 bits    12 bits
```

| Field      | Bits |        Range | Purpose                                        |
| ---------- | ---: | -----------: | ---------------------------------------------- |
| sign       |    1 |          `0` | Keeps the original Java/Scala `Long` positive  |
| timestamp  |   41 | `0 .. 2⁴¹-1` | Milliseconds since Twitter's custom epoch      |
| datacenter |    5 |    `0 .. 31` | Which data center generated it                 |
| worker     |    5 |    `0 .. 31` | Which generator inside that DC                 |
| sequence   |   12 |  `0 .. 4095` | Multiple IDs generated in the same millisecond |

How many days is that timestamp? ~70 years with 41 bits of info.

Rest 32 x 32 = 1024 machines, each one for the SAME millisecond can generated 4096 messages.

```
id =
    ((timestamp - epoch) << 22)
  | (datacenterId << 17)
  | (workerId << 12)
  | sequence
```

## Generation algo each worker runs

Two states are needed, `lastTimestamp` and `sequence`. On each generation, check if timestampe has change, if it has clear seq, if not increment sequence numbers.

if the seq limit is reached and timestamp has not changed, you just wait.

## Collision

Assumption: no two workers think that they belong to same datacenter and have same worker id.

Under this, a collision can only happen if there are 4096 ids generated per millisecond
=> 4,096,000 ids / sec / worker which is a reasonable assumption.

An overload is handled by a tiny busy wait.

## NTP correction

This explains the clock model in systems that's common

```
             Internet time servers
                    │
                   NTP
                    │
                    ▼
┌──────────┐    ┌──────────────┐
│ Hardware │───▶│ System clock │───▶ 2026-09-16 00:42:31
│ RTC      │    │ ("wall time")│
└──────────┘    └──────────────┘
     ▲
     │
small battery
```

The hardware clock is not perfect and over months, can accumulate several seconds of drift.
The system clock hence sync both with RTC and using a NTP ( network time protocol )

OSes also have a "monotonic" clock which is for such monotonse uses at system level
like durations, but that has drifts as well, so you DO need NTP.

What if the clock goes backwards then? from an NTP correction? We store `lastTimestamp` and
just throw if `currentTime()` ever goes behind `lastTimestamp` to avoid backward corrections.

## What's the "catch"?

Worker idenity is a hard assumption, in distributed / replicated systems with clock correction scenarios, this NEEDS those cases to be handled outside of snowflake.

### State of things now?

There are obvious advantages over something like random UUIDv4 and it might look like that "time-ordering" is the biggest thing it offers, which was true for the time.

However, UUIDv7 also offers time ordering and only loses on the fact that it's 128bit.
In most scenarios, you would use something like UUIDv7 to avoid any issues with worker
idenity at all.

```
Need compact BIGINT ( 64bit )?
        │
       yes
        ↓
Snowflake-style ID
        │
        └─ you must solve worker identity + clock handling


Don't care about 64-bit?
        │
       yes
        ↓
UUIDv7
        │
        └─ standardized, easier decentralized deployment
```

## Summary

**time prefix + namespace partitioned middle + counter suffix**

But a relic of it's time, UUIDv7 should be the goto now given that storage is generally
not a concern.
