# Stock price fluctuation

You have a stock which can get updates for restrospecitive timestamps. You need to answer
min and max across all ranges as well as the latest timestamp price.

## Solution

I was initially thinking along the lines of a segment tree which would work but is a more
general solution than the problem demands. Note that you can you a heap if you can handle
lazy deletion.

The general idea for lazy deletion is to maintain a global truth somewhere and have
enough state in the heap to be able to verify after a pop.

> rem to always reach out for this instead of your segment tree bias when rmqs are over a
> full range

```python
class StockPrice:

    def __init__(self):
        self.mn_h, self.mx_h = [], []
        # max t so far
        self.latest_t = -math.inf
        # price at a timestamp
        self.price = {}

    def update(self, timestamp: int, price: int) -> None:
        self.latest_t = max(self.latest_t, timestamp)
        self.price[timestamp] = price
        # timestamp is just for state verification
        heapq.heappush(self.mn_h, (price, timestamp))
        heapq.heappush(self.mx_h, (-price, timestamp))

    def current(self) -> int:
        return self.price[self.latest_t]

    def maximum(self) -> int:
        while self.mx_h:
            p, t = self.mx_h[0]
            p = -p

            # it's some max and it matches the global truth
            if self.price[t] == p:
                return p
            else:
                heapq.heappop(self.mx_h)

        raise Exception("should not happen")

    def minimum(self) -> int:
        while self.mn_h:
            p, t = self.mn_h[0]
            if self.price[t] == p:
                return p
            else:
                heapq.heappop(self.mn_h)

        raise Exception("should not happen")
```
