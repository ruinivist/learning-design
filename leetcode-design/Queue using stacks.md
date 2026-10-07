# Queue using 2 stacks

The idea is that each push or peak does a double transfer, one transfer reverses the order
so we do too otherwise complicated casing will be needed.

```python
class MyQueue:

    def __init__(self):
        self.len = 0
        self.pri = []
        self.sec = []

    def push(self, x: int) -> None:
        self.pri.append(x)
        self.len += 1

    def pop(self) -> int:
        for _ in range(self.len - 1):
            self.sec.append(self.pri.pop())
        x = self.pri.pop()
        self.len -= 1
        for _ in range(self.len):
            self.pri.append(self.sec.pop())
        return x

    def peek(self) -> int:
        for _ in range(self.len):
            self.sec.append(self.pri.pop())
        x = self.sec[-1]
        for _ in range(self.len):
            self.pri.append(self.sec.pop())
        return x

    def empty(self) -> bool:
        return self.len == 0
```

# The better O(1) pop and peek solution

The key idea is that one transfer reverse orders. So the deque can be worked with just like
a stack as top will be older. But you only do that transfer when a pop is called and you
are empty ( having nothing in out stack ).

In stack is for push elements, outstack is for pop and peek. We only move from in to out
when out is empty.

```python
class MyQueue:

    def __init__(self):
        self.in_stack = []
        self.out_stack = []

    def push(self, x: int) -> None:
        self.in_stack.append(x)

    def pop(self) -> int:
        self._move()
        return self.out_stack.pop()

    def peek(self) -> int:
        self._move()
        return self.out_stack[-1]

    def empty(self) -> bool:
        return not self.in_stack and not self.out_stack

    def _move(self):
        if not self.out_stack:
            while self.in_stack:
                self.out_stack.append(self.in_stack.pop())
```
