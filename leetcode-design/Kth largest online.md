# Kth largest in data stream

Kind of like a complement of the median in data stream except since you have you
k fixed as opposed to it changing based on total length ( as was the case with median one ), you can just keep one heap.

Since you need the smallest of the set I maintain, it'll a min heap.
A pop will remove the smallest element, we would only want that when size is > k so
then the set is only the top k values.

```python
class KthLargest:

    def __init__(self, k: int, nums: list[int]):
        self.q = nums
        self.k = k
        heapq.heapify(self.q)
        while len(self.q) > k:
            heapq.heappop(self.q)

    def add(self, val: int) -> int:
        heapq.heappush(self.q, val)
        # the init list can have < k elems
        if len(self.q) > self.k:
            heapq.heappop(self.q)
        return self.q[0]
```
