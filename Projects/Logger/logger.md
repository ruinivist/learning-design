# Logger design

`LogManager` owns a logger hierarchy and one shared `Dispatcher`. Loggers admit records and route them through attached sinks; sinks delegate representation to formatters.

These notes cover [logger.py](logger.py). Use the [breakdown](logger-breakdown.md) to rebuild the design by responsibility.

![Logger UML class diagram](logger-uml.svg)

## Reading the UML

1. Start with `LogManager`. It creates the root, dispatcher, clock, logger registry, and lock. `get_logger("app.api")` creates or reuses `app` and `app.api` under that lock, connecting each node to its parent.
2. Follow `Logger`. It keeps a parent reference, an optional level, a propagation flag, and a tuple of sinks. `effective_level()` walks toward the root until it finds an explicit level; the manager gives the root `WARN` by default.
3. Connect `Record`. After admission, `log()` captures the logger name, level, clock value, message template, and argument tuple. Its fields are frozen, and `message()` applies `%` interpolation when a formatter needs the text.
4. Follow `Dispatcher`. Its bounded queue holds `(Logger, Record)` pairs. One worker dequeues each pair and calls that logger's `handle()`.
5. Follow delivery to sinks. `handle()` notifies local sinks, then calls the parent's `handle()` when `propagate` is true. Each `Sink.emit()` applies its own level threshold and formatter before calling the destination's `write()`.
6. Follow the two extension points. `PlainFormatter` and `JsonFormatter` implement `Formatter`; `ConsoleSink`, `FileSink`, and `MemorySink` implement `Sink.write()`. Formatting and output destinations can vary independently.

## Happy path

1. Create a manager, set `manager.root.level = Level.INFO`, attach a `ConsoleSink` to the root, and obtain `app.api` through `get_logger()`.
2. Call `logger.info("request %s", "ok")`. `log()` finds the inherited `INFO` threshold, reads the clock, and builds a `Record` with origin `app.api`.
3. With queue space below the drop threshold, `Dispatcher.submit()` enqueues the logger and record. The caller returns without waiting for output.
4. The worker dequeues the pair and calls `app.api.handle(record)`. Local notification runs first, then propagation reaches `app`, then the root.
5. The root's console sink accepts the record. `PlainFormatter.format()` calls `record.message()` and adds the timestamp, level name, and origin; `ConsoleSink.write()` prints the line to its stream, which defaults to standard error.
6. The worker calls `task_done()`. `manager.flush()` waits for queued work to finish. Once producers have stopped, `manager.shutdown()` queues a stop sentinel, joins the worker, and closes each distinct currently attached sink.

## Design choices

- Logger levels control admission; sink levels control destinations. Parent logger levels are not checked again during propagation. Set `propagate = False` to stop after a node's local sinks.
- Deferred interpolation moves formatting to the worker and avoids formatting rejected records. Every accepting sink formats separately. Frozen `Record` fields do not freeze mutable objects inside `args`; callers must keep them stable until delivery.
- `capacity` must be positive. The drop threshold is `capacity - capacity // 5`: with capacity 10, DEBUG/INFO submissions start dropping when the observed queue size reaches 8. WARN/ERROR submissions use blocking `put()` regardless of that threshold.
- Queue-size checks are approximate under contention. Even a DEBUG/INFO submission that passes the check can block if other producers fill the queue first. `dropped` counts only overload drops, and its unlocked increments can undercount.
- The injected clock supplies timestamps; the default returns timezone-aware UTC values. The manager is an ordinary instance, so separate managers have separate hierarchies and workers.
- `FileSink` opens an append-mode UTF-8 file. `MemorySink` stores formatted strings. `flush()` waits for queue task completion; it does not flush file buffers or make output durable. File closure happens during shutdown.

## Design patterns

| Pattern | Where | Purpose |
| --- | --- | --- |
| Strategy | `Formatter`, `PlainFormatter`, `JsonFormatter` | Choose representation independently of the output destination. |
| Template Method | `Sink.emit()` calls `write()` | Share threshold checking and formatting while subclasses supply writing. |
| Observer | `Logger.attach()`, `detach()`, `notify()` | Deliver the same record to every attached sink. |
| Chain of Responsibility | `Logger.handle()` calls its parent | Continue delivery through ancestors when propagation is enabled; several nodes can handle one record. |

## Design principles

| Principle | Where / how |
| --- | --- |
| Single responsibility | The manager builds the hierarchy, the dispatcher schedules delivery, loggers route records, formatters render, and sinks write. |
| Open/closed | New sink and formatter subclasses use the existing delivery path. |
| Dependency inversion | Loggers use the `Sink` contract; sinks use the `Formatter` contract. Callers choose concrete implementations during setup. |

## Concurrency

| Concern | Implementation |
| --- | --- |
| Duplicate logger creation | The manager lock covers registry lookup and creation of the complete dotted-name path. |
| Output ordering | A thread-safe queue feeds one worker per manager. Delivery follows enqueue order; concurrent producers' timestamps need not have that order. |
| Sink failure | `notify()` catches each sink's `emit()` exception and reports it to standard error, then continues with other sinks and parents. Failed output is not retried. |
| Configuration changes | Replacing the sink tuple keeps an active iteration stable. Attach/detach, levels, formatters, and propagation are otherwise unsynchronized; configure before concurrent use. |
| Flush | `Queue.join()` waits for outstanding tasks. Ongoing producers can extend the wait; it is not a producer barrier. |
| Shutdown | Stop producers first: the closed check and enqueue are not atomic, so a racing submission can land after the stop sentinel. Call shutdown once; later submissions are silently ignored. |
| Worker lifetime | The worker is a daemon. Process exit can discard queued records without explicit shutdown. A sink must not call `flush()` or `shutdown()` on its own worker. |

## Common mistakes

- Set the root level explicitly if INFO or DEBUG records should be admitted; its initial level is WARN. Keep an explicit root level so inheritance has a stopping point.
- Avoid attaching the same sink at several hierarchy levels unless duplicate output is intended. Sinks can be shared, so attachment does not imply exclusive ownership.
- Keep message arguments unchanged until delivery. An interpolation error is handled as a sink failure, and that sink produces no line.
- Stop producers before draining and shutting down. Keep attached sinks fixed through shutdown so the manager can close them after the worker exits.
- Use a sink's level to filter propagated records. Changing an ancestor's logger level does not filter a record already admitted by a child.
