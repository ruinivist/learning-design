# Stack with increment operation

It's the usual except, you need a range increment on the bottom k elements.
Initially I was thinking of using a fenwick tree with delta updates and then applying that range
updated on the element lazily at query time but I missed that we can do better by virtue of this
problem being applied on a stack, and hence knowing that we at any point in time can only be
querying the last element.

Two observations,

- a delta applied in the prefix won't matter to me if I'm ahead of it, so I MUST not handle or do any
  processing if I'm ahead.
- as I go back (pop) I can ONLY be interting with a possible delta, which MUST be carried over when I pop
  and MUST be undone if I push, so semantics are as if the incs are done on elems in the prefix.

So this idea works,

- when you increment, put in +delta
- when you go back via pop, apply the delta as lazy += delta AND decrease the delta forever too
- when you go ahead via a push, apply it as a lazy -= delta

## Refining again

the impl was a bit well less than ideal and buggy, need to define properpy

- lazy = pending inc on CURRENT top
- deltas[i] == pending inc between i and i+1

So on a pop you add a delta[i-1] and a push you add delta[i]

```python
class CustomStack:

    def __init__(self, maxSize: int):
        self.cap = maxSize
        self.stk = []
        self.lazy = 0
        self.deltas = [0] * maxSize

    def push(self, x: int) -> None:
        if len(self.stk) < self.cap:
            idx = len(self.stk) - 1

            if idx >= 0:
                self.deltas[idx] = self.lazy
                self.lazy -= self.deltas[idx]

            self.stk.append(x)

    def pop(self) -> int:
        if not self.stk:
            return -1

        idx = len(self.stk) - 1
        ans = self.stk.pop() + self.lazy

        if idx > 0:
            self.lazy += self.deltas[idx - 1]
            self.deltas[idx - 1] = 0
        else:
            self.lazy = 0

        return ans

    def increment(self, k: int, val: int) -> None:
        k = min(k, len(self.stk))

        if k <= 0:
            return

        if k == len(self.stk):
            self.lazy += val
        else:
            self.deltas[k - 1] += val

```

## Refining yet again

I've complicated the problem, the ideal solution does not manage any global lazy and instead just
defines delta(i) to be what you need to apply for all elems i and below.
So when you pop on i, you add it but since the elems that the delta was applied to are now gone, you
ALSO shift the delta, carrying it with you.

This way the handling becomes really really simple and isolated to just pop.

```python
class CustomStack:

    def __init__(self, maxSize: int):
        self.cap = maxSize
        self.stk = []
        self.inc = [0] * maxSize

    def push(self, x: int) -> None:
        if len(self.stk) < self.cap:
            self.stk.append(x)

    def pop(self) -> int:
        if not self.stk:
            return -1

        # ret val
        i = len(self.stk) - 1
        val = self.stk.pop() + self.inc[i]

        # shift delta to one less and make current one 0
        if i > 0:
            self.inc[i - 1] += self.inc[i]
        self.inc[i] = 0

        return val

    def increment(self, k: int, val: int) -> None:
        i = min(k, len(self.stk)) - 1

        if i >= 0:
            self.inc[i] += val
```
