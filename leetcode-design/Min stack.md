# Min Stack

I was kinda glossing over this problem since I assumed it's some trivial monostack problem,
well it is but not too trivial, I guess.

I need a min stack so if I have a stack where at the top I keep the smallest element ( as I go
from left to right in the stack so the stk is mono deq ), then if I pop from stack and elem in my
mono dq matches then I also pop from that.

```python
class MinStack:

    def __init__(self):
        self.min = []
        self.stk = []

    def push(self, value: int) -> None:
        self.stk.append(value)

        if not self.min or value <= self.min[-1]:
            self.min.append(value)

    def pop(self) -> None:
        val = self.stk.pop()
        if self.min[-1] == val:
            self.min.pop()

    def top(self) -> int:
        return self.stk[-1]

    def getMin(self) -> int:
        return self.min[-1]

```

> I was kind of misremembering that I needed like a while loop or something, this isn't small to left
> or right like problem
