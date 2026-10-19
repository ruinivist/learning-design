# you need this at first
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import IntEnum
import json
import queue
import sys
import threading
from typing import Any, TextIO


class Level(IntEnum):
    DEBUG = 10
    INFO = 20
    WARN = 30
    ERROR = 40

@dataclass(frozen=True, kw_only=True)
class Record:
    origin: str
    level: Level
    ts: datetime
    msg: str
    args: tuple[Any,...] = ()

    def message(self) -> str:
        return self.msg % self.args if self.args else self.msg

# === formatter strategy

class Formatter(ABC):
    @abstractmethod
    def format(self, r: Record) -> str: ...

class PlainFormatter(Formatter):
    def format(self, r):
        return f"{r.ts.isoformat()} {r.level.name} {r.origin}: {r.message()}"

class JsonFormatter(Formatter):
    def format(self, r):
        return json.dumps({"ts": r.ts.isoformat(), "level": r.level.name, "logger": r.origin, "msg": r.message()})

# === sink is where data ends up for the actual writing, think of as the "Appender"

class Sink(ABC):
    # the * means that every param after MUST be named arg
    def __init__(self, *, level: Level = Level.DEBUG, formatter: Formatter | None = None) -> None:
        self.level = level
        # why not just put in the arg as instead of None there
        # that line would run one when the class itself is created, every default formatter then would be the
        # same object by identity, modifying one changes the other
        self.formatter = formatter or PlainFormatter()

    def emit(self, r: Record) -> None:
        # int enums you can compare like this
        if r.level >= self.level:
            self.write(self.formatter.format(r))

    @abstractmethod
    def write(self, line: str) -> None: ...

    def close(self) -> None: ...

# the 3 actual sink impls

class ConsoleSink(Sink):
    # in general we don't construct objects unless "immutable"ish in args
    def __init__(self, *, stream: TextIO | None = None, **kw: Any) -> None:
        super().__init__(**kw)
        # when values are Falsy, you can do this as a FirstNonError
        self.stream = stream or sys.stderr

    def write(self, line):
        print(line, file=self.stream)

class FileSink(Sink):
    def __init__(self, *, path: str, **kw):
        super().__init__(**kw)
        # default encoding is what the machine's locale
        self.file = open(path, "a", encoding="utf-8")

    def write(self, line):
        # you could also do
        # self.file.write(line + "\n")
        print(line, file = self.file )

    def close(self):
        # rem: here we do need a close
        self.file.close()

class MemorySink(Sink):
    def __init__(self, **kw: Any):
        super().__init__(**kw)
        self.lines: list[str] = []

    def write(self, line):
        self.lines.append(line)

# === dispatcher

# a dispatcher just "detaches the write" to an async path. Logger will only add to queue ( blocking ) and let
# dispatcher do the eventual actual write

# to id match for a stop
_STOP = object()

class Dispatcher:
    def __init__(self, *, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("capacity must be positive")

        # this is a thread safe queueu
        self.q: queue.Queue[Any] = queue.Queue(maxsize=capacity)
        self.capacity_threshold = capacity - capacity // 5
        self.dropped = 0
        self.closed = False
        # daemon=True? at exist python does an auto join for all non daemon threads, an error where the program
        # exist without doing a graceful shutdown, it'll be stuck forever
        self.thread = threading.Thread(target=self._run, name="dispatcher", daemon=True)
        self.thread.start()

    def _run(self) -> None:
        # unfort, walrus doesn't unpack
        while (item := self.q.get()) is not _STOP:
            logger, r = item
            logger.handle(r)
            self.q.task_done()
        # q.join would be blocked until all task dones are called
        self.q.task_done()

    def submit(self, logger: Logger, r: Record) -> None:
        # closed check and put aren't atomic, a record racing shutdown can be lost
        if self.closed:
            return
        # custom dropping logic for in capacity, if debug or info, drop it
        # else blocking wait
        if r.level < Level.WARN and self.q.qsize() >= self.capacity_threshold:
            self.dropped += 1  # unlocked, can undercount under contention; it's a metric
            return
        self.q.put((logger, r))

    def flush(self) -> None:
        self.q.join()

    def shutdown(self) -> None:
        self.closed = True
        self.q.put(_STOP)
        self.thread.join()

# === Logger -> Observer pattern for sinks and Chain pattern for handlers

class Logger:
    def __init__(self, *, name: str, parent: Logger | None, dispatcher: Dispatcher, clock: Callable[[], datetime]) -> None:
        self.name = name
        self.parent = parent # for the chain
        self.dispatcher = dispatcher
        self.clock = clock
        self.level: Level | None = None # it'll fall back to parent first

        # same message is logged by EACH handler
        self.propagate = True
        self.sinks : tuple[Sink, ...] = () # tuple[Sink] would mean just one elem

    def attach(self, sink: Sink) -> None:
        # 1\ we made it a tuple so that the notify loop is not run under changing list and accidentally
        # skip a valid sink ( since indexes changed )
        self.sinks = (*self.sinks, sink)

    def detach(self, sink: Sink) -> None:
        self.sinks = tuple(s for s in self.sinks if s is not sink)

    def effective_level(self) -> Level:
        if self.level is not None:
            return self.level
        return self.parent.effective_level()

    def log(self, level: Level, msg: str, *args: Any) -> None:
        if level < self.effective_level():
            return
        self.dispatcher.submit(self, Record(origin=self.name, level=level, ts=self.clock(), msg=msg, args=args))

    def debug(self, msg: str, *args: Any) -> None: self.log(Level.DEBUG, msg, *args)
    def info(self, msg: str, *args: Any) -> None: self.log(Level.INFO, msg, *args)
    def warn(self, msg: str, *args: Any) -> None: self.log(Level.WARN, msg, *args)
    def error(self, msg: str, *args: Any) -> None: self.log(Level.ERROR, msg, *args)

    ### these below are all on the writer thread
    def notify(self, r: Record) -> None:
        for sink in self.sinks:
            try:
                sink.emit(r)
            except Exception as e:
                # one broken sink must not starve the others or kill the writer thread
                print(f"log sink {type(sink).__name__} failed: {e!r}", file=sys.stderr)

    # threads will call handle to do the chain propagation
    def handle(self, r: Record) -> None:
        self.notify(r)
        if self.propagate and self.parent is not None:
            self.parent.handle(r)

# composition root

class LogManager:
    # not an enforced singleton at structual level, the code usage make it singleton
    def __init__(self, *, capacity: int = 1024,
                 clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc)) -> None:
        self.dispatcher = Dispatcher(capacity=capacity)
        self.clock = clock
        self.root = Logger(name="root", parent=None, dispatcher=self.dispatcher, clock=clock)
        self.root.level = Level.WARN  # stdlib's default too
        self.loggers: dict[str, Logger] = {}
        self.lock = threading.Lock()

    def get_logger(self, name: str) -> Logger:
        # we fetch or create under a lock
        # also need to ensure every logger exists in the path
        with self.lock:
            node, parts = self.root, name.split(".")
            # assumes path do not have root, path is "app" even when "root.app" is the internal
            # one technically
            path = ""
            for part in parts:
                path = f"{path}.{part}" if path else part
                if path not in self.loggers:
                    # all of them share the dispatcher and the clock
                    self.loggers[path] = Logger(name=path, parent=node, dispatcher=self.dispatcher, clock=self.clock)
                node = self.loggers[path]

            return node

    # this is a dispatcher event
    def flush(self) -> None:
        self.dispatcher.flush()

    def shutdown(self) -> None:
        self.dispatcher.shutdown()
        # this is python magika for each logger, for each sink in that, make a set out of it
        # fine to not lock as no more calls to sink emit are handled by the dispatcher
        # though someone CAN add a filesink post this and it won't be closed
        with self.lock:
            sinks = {s for lg in (self.root, *self.loggers.values()) for s in lg.sinks}
        for sink in sinks:
            sink.close()
