# Time based kv store

For the same key, you need to store values at different timestamps and be able to retrieve them
as of time.

You can't just do a hashmap as timestamp can be any >= than a set timestamp.
One way would be keeping to keep it as (time, value) tuples as time is always increasing you can then
just bin search. This you would need for each key.

```python
class TimeMap:

    def __init__(self):
        self.kv = defaultdict(list)

    def set(self, key: str, value: str, timestamp: int) -> None:
        # expected to be called with increasing timestamps for a key
        self.kv[key].append((timestamp, value))

    def get(self, key: str, timestamp: int) -> str:
        vals = self.kv[key]
        # I need largest t <= timestamp
        idx = bisect_right(vals, timestamp, key=lambda x: x[0]) - 1
        return vals[idx][1] if idx >= 0 else ""
```
