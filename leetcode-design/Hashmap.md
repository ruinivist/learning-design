# Design hasmap

The problem on the platform is kind of simple, but let's make it harder

- use a non identity hash function
- probing can be different
- resize based on load factor

Here's my original

```python
class MyHashMap:

    def __init__(self):
        self.kResizeThreshold = 0.75
        self.buckets = [[] for _ in range(8)]
        self.len = 0

    def _load_factor(self):
        return self.len / len(self.buckets)

    def _hash(self, key):
        return key % len(self.buckets)

    def _put_internal(self, key, value):
        idx = self._hash(key)

        for bidx, (k, v) in enumerate(self.buckets[idx]):
            if k == key:
                self.buckets[idx][bidx] = (key, value)
                return

        self.buckets[idx].append((key, value))
        self.len += 1

    def _resize(self):
        old = self.buckets
        self.buckets = [[] for _ in range(2 * len(old))]
        self.len = 0

        for bucket_items in old:
            for k, v in bucket_items:
                self._put_internal(k, v)

    def put(self, key: int, value: int) -> None:
        self._put_internal(key, value)

        if self._load_factor() > self.kResizeThreshold:
            self._resize()

    def get(self, key: int) -> int:
        idx = self._hash(key)

        for k, v in self.buckets[idx]:
            if k == key:
                return v

        return -1

    def remove(self, key: int) -> None:
        idx = self._hash(key)

        for bidx, (k, v) in enumerate(self.buckets[idx]):
            if k == key:
                self.buckets[idx].pop(bidx)
                self.len -= 1
                return
```

And here's a more pythonic version I asked chatgpt to make

```python
from itertools import chain


class MyHashMap:
    MAX_LOAD_FACTOR = 0.75
    INITIAL_CAPACITY = 8

    def __init__(self):
        self.buckets: list[list[tuple[int, int]]] = [
            [] for _ in range(self.INITIAL_CAPACITY)
        ]
        self.size = 0

    def __len__(self):
        return self.size

    def _bucket(self, key):
        return self.buckets[hash(key) % len(self.buckets)]

    def _put_internal(self, key, value):
        bucket = self._bucket(key)

        for i, (k, _) in enumerate(bucket):
            if k == key:
                bucket[i] = (key, value)
                return

        bucket.append((key, value))
        self.size += 1

    def _resize(self):
        old_buckets = self.buckets
        self.buckets = [[] for _ in range(2 * len(old_buckets))]
        self.size = 0

        for key, value in chain.from_iterable(old_buckets):
            self._put_internal(key, value)

    def put(self, key: int, value: int) -> None:
        if (self.size + 1) / len(self.buckets) > self.MAX_LOAD_FACTOR:
            self._resize()

        self._put_internal(key, value)

    def get(self, key: int) -> int:
        return next(
            (v for k, v in self._bucket(key) if k == key),
            -1,
        )

    def remove(self, key: int) -> None:
        bucket = self._bucket(key)

        for i, (k, _) in enumerate(bucket):
            if k == key:
                del bucket[i]
                self.size -= 1
                return
```
