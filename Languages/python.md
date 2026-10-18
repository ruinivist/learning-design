# Enough of python to implement most programs and write better code

## Abstract classes

```python
from abc import ABC, abstractmethod

class Shape(ABC):
    # order matters, it becomes abstract first and then a property
    @property
    @abstractmethod
    def area(self) -> float: ...

    @abstractmethod
    def perimeter(self) -> float: ...
```

Note:

- if you swap order, it raises
- you NEED to still use @property on the impls as well

## Dataclasses

There is no default init if you don't specify, the init NEEDS those args

```python
@dataclass(slots=True, kw_only=True)
class SlidingWindowState:
    request_times: list[int]
```

will raise if you do `SlidingWindowState()`.
What you instead want is `request_times: list[int] = field(default_factory=list)`

**What if this was a class?**

```python
class SlidingWindowState:
    def __init__(self) -> None:
        self.request_times: list[int]
```

Just this above is only a type hint, nothing else, not even `None`.

## Default values on sets

`set.set_default(key, value)`
