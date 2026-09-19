# Outbox + Relay

This is a common pattern to handle atomicity in the case of sql + stream write.

For example, let's say I want an event to be emitted when a new tweet is created
in db; this event is meant to be consumed downstream. There are two failures
cases given the entire thing cannot be "atomic" => two services here, sql db +
say kafka.

Outbox is just having an outbox table in db for such events and then write to
both atomically. This way the event's persistence is mapped to the data itself.

Then a relay is a separate service ( but usually paired with an outbox ) that
then pushes those events to kafka and retries if needed.
