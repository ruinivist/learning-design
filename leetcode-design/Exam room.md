# Exam room

Think of each student sitting "breaking" a partition.
You basically want to seat at the middle of the longest partition and then split it
and push it back into a priority queue.

Now with this, finding where to seat is trivial but when a student gets up and leaves,
then you need to find the left interval extent, the right interval extent and then merge
and push those; deleting the smaller left and right ones would be a lazy deletion.
This above is a bit tricky but here's an idea, when a student gets up I know the right end
for the left interval and the left end for the right interval, both can be uniquely identified
from those two ends, so just store this info for each end in separate maps.
It also handles the lazy deletion as when you pop, try to match if the left and right ends with
what the map has, to know if it's up to date.

The trick case is the start end end handling. If any any point in time, the 0th index is free then you
place there, else if the n-1 ( last ) index is free then you place there.

**edge case** as just this above won't work
I need to find the min index seat so just by picking the larger size it won't work, consider cases where
lenghts are 3 and 4, due to rounding nearest would be same for either case but if the 3 ones has smaller
index then that is the one to pick.
The solution is to use the distances POST split instead as in what would the min dist be if I use this
segment.

## Avoiding an implementation hell

The general idea above is correct but I need to be careful. Implementing on my own I'll run into
a LOT of edge cases so better to remember bits of the impl below.

- have a separate add and remove function
- to the casing in a best function

The rest then becomes a very clean impl

```python
import heapq

class ExamRoom:
    def __init__(self, n: int):
        self.n = n
        self.heap = []

        # left boundary -> right boundary
        self.right = {}

        # right boundary -> left boundary
        self.left = {}

        self.add(-1, n)

    def best(self, l, r):
        if l == -1:
            return r, 0

        if r == self.n:
            return self.n - 1 - l, self.n - 1

        return (r - l) // 2, (l + r) // 2

    def add(self, l, r):
        self.right[l] = r
        self.left[r] = l

        if r - l > 1:
            dist, seat = self.best(l, r)
            heapq.heappush(self.heap, (-dist, seat, l, r))

    def remove(self, l, r):
        del self.right[l]
        del self.left[r]

    def seat(self) -> int:
        while True:
            _, p, l, r = heapq.heappop(self.heap)

            if self.right.get(l) == r:
                break

        self.remove(l, r)

        self.add(l, p)
        self.add(p, r)

        return p

    def leave(self, p: int) -> None:
        l = self.left[p]
        r = self.right[p]

        self.remove(l, p)
        self.remove(p, r)

        self.add(l, r)
```
