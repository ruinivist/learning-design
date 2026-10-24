# Chain of responsibility

The pattern is called Chain of Responsibility. A request moves through linked handlers; each handler decides whether to handle it or pass it on.

- Request: the data passed through the chain.
- Handler: knows its next handler and exposes `handle(request)`.
- Concrete handler: decides whether it can handle the request.
- Client: builds the chain and sends requests to its first handler.

## Python

Two common forms:

- Stop after handling: the first handler that accepts the request ends the chain.
- Handle and forward: each handler can do work, then pass the request onward. Logger propagation uses this form; `propagate = False` stops it.

This template stops after the first match. `handle()` returns `True` when a handler accepts the request, or `False` if the chain ends without a match.

```python
from __future__ import annotations

from abc import ABC, abstractmethod


class Handler(ABC):
    def __init__(self, next_handler: Handler | None = None):
        self.next_handler = next_handler

    def handle(self, request: str) -> bool:
        if self.try_handle(request):
            return True
        if self.next_handler is not None:
            return self.next_handler.handle(request)
        return False

    @abstractmethod
    def try_handle(self, request: str) -> bool:
        pass


class HelpHandler(Handler):
    def try_handle(self, request: str) -> bool:
        if request != "help":
            return False
        print("Available requests: help, status")
        return True


class StatusHandler(Handler):
    def try_handle(self, request: str) -> bool:
        if request != "status":
            return False
        print("Service is running")
        return True


chain = HelpHandler(StatusHandler())

assert chain.handle("help") is True
assert chain.handle("status") is True
assert chain.handle("unknown") is False
```

The client only calls the first handler. Each handler knows its successor, so adding another handler changes the chain setup without changing the client call.

Order matters: if several handlers could accept a request, the first one wins. Keep the links acyclic and build them before using the chain. Exceptions propagate to the caller; an error is different from an unhandled request.
