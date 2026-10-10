# Median from data stream

I quite rememeber this problem at this point, the idea that you use two heaps such that they
are partitioned around the running median.

Followup:

- if all integers are in range [0,100], can we do better?

## Solution

This uses the idea of a norm step and a biased push on high.

```python
import heapq


class MedianFinder:
    def __init__(self):
        self.low = []
        self.high = []

    def addNum(self, num: int) -> None:
        # always push to high and normalise later
        heapq.heappush(self.high, num)
        self.normalize()

    def normalize(self):
        # Fix sizes, can only be impabalanced by high
        if len(self.high) > len(self.low) + 1:
            heapq.heappush(self.low, -heapq.heappop(self.high))

        # Now that elem sizes are correct, only order can be wrong
        # why swap? well if order is wrong on one end, it must be
        # swapped from the ohter
        if self.low and -self.low[0] > self.high[0]:
            a = -heapq.heappop(self.low)
            b = heapq.heappop(self.high)

            heapq.heappush(self.low, -b)
            heapq.heappush(self.high, a)

    def findMedian(self) -> float:
        if len(self.high) > len(self.low):
            return self.high[0]

        return (self.high[0] - self.low[0]) / 2
```

A simpler impl along the same idea is this where you strip the conditionals and
do a biased push to high, and then an optional move to fix sizes.

> NOTE: PREFER THIS SOLUTION

```python
import heapq

class MedianFinder:
    def __init__(self):
        self.low = []   # max heap
        self.high = []  # min heap

    def addNum(self, num: int) -> None:
        heapq.heappush(self.high, num)

        # Move smallest from high to low
        heapq.heappush(self.low, -heapq.heappop(self.high))

        # Balance sizes
        if len(self.low) > len(self.high):
            heapq.heappush(self.high, -heapq.heappop(self.low))

    def findMedian(self) -> float:
        if len(self.high) > len(self.low):
            return float(self.high[0])

        return (self.high[0] - self.low[0]) / 2.0
```

Note that the biased push and non-conditional pop guarantees correct ordering. All we then
do is balance sizes if needed.

Another ordering strategy is to push based on sizes, if total size is odd, then low has
1 more elem, so we push to high to correct the sizes. This can lead to AT MAX 1 swap being
wrong which we fix. Same in the other direction.

```python
def addNum(self, num):
    if self.n % 2 == 0:
        heapq.heappush(self.high, num)
        heapq.heappush(
            self.low, -heapq.heappop(self.high)
        )
    else:
        heapq.heappush(self.low, -num)
        heapq.heappush(
            self.high, -heapq.heappop(self.low)
        )

    self.n += 1
```
