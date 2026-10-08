# Desing circular queue

As long as you remember the idea of full being when end + 1 is same as start aka if you move one past you are at start.

```python
class MyCircularQueue:

    def __init__(self, k: int):
        self.start, self.end = 0, 0
        self.n = k + 1
        self.arr = [0] * self.n

    def enQueue(self, value: int) -> bool:
        if self.isFull():
            return False

        self.arr[self.end] = value
        self.end = (self.end + 1) % self.n
        return True

    def deQueue(self) -> bool:
        if self.isEmpty():
            return False

        val = self.arr[self.start]
        self.start = (self.start + 1) % self.n
        return True

    def Front(self) -> int:
        if self.isEmpty():
            return -1
        return self.arr[self.start]

    def Rear(self) -> int:
        if self.isEmpty():
            return -1
        end = (self.end - 1 + self.n) % self.n
        return self.arr[end]

    def isEmpty(self) -> bool:
        return self.start == self.end

    def isFull(self) -> bool:
        return ((self.end + 1) % self.n) == self.start
```
