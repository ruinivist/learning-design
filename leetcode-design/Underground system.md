# Design underground system

This is an online average calculator of sorts. Just some things to watch for

- edges are directed
- pending travels are not to be counted

```python
class UndergroundSystem:

    def __init__(self):
        # for customer = (start time, start station)
        self.pending = {}
        # for (start,end) tuples = (count, sum)
        self.stats = {}

    def checkIn(self, id: int, stationName: str, t: int) -> None:
        self.pending[id] = (t, stationName)

    def checkOut(self, id: int, stationName: str, t: int) -> None:
        startTime, startStation = self.pending[id]
        del self.pending[id]
        delta = t - startTime

        key = (startStation, stationName)
        count, tsum = self.stats.get(key, (0, 0))
        self.stats[key] = (count + 1, tsum + delta)

    def getAverageTime(self, startStation: str, endStation: str) -> float:
        # assume key is there
        key = (startStation, endStation)
        count, tsum = self.stats.get(key)
        return tsum / count
```
