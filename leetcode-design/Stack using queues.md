# Stack using 2 queues

this is simple

```python
from queue import Queue


class MyStack:

    def __init__(self):
        self.size = 0
        self.pri = Queue()
        self.sec = Queue()

    def push(self, x: int) -> None:
        self.size += 1
        self.pri.put(x)

    def pop(self) -> int:
        for _ in range(self.size - 1):
            self.sec.put(self.pri.get())

        x = self.pri.get()

        self.pri, self.sec = self.sec, self.pri
        self.size -= 1

        return x

    def top(self) -> int:
        x = self.pop()
        self.push(x)
        return x

    def empty(self) -> bool:
        return self.size == 0
```

# Stack using 1 queue

The idea is to rotate the queue after each push so that the newest is at front.

```python
from queue import Queue


class MyStack:

    def __init__(self):
        self.q = Queue()

    def push(self, x: int) -> None:
        self.q.put(x)

        # Move all previous elements behind x
        for _ in range(self.q.qsize() - 1):
            self.q.put(self.q.get())

    def pop(self) -> int:
        return self.q.get()

    def top(self) -> int:
        return self.q.queue[0]

    def empty(self) -> bool:
        return self.q.empty()
```
