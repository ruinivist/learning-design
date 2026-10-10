# LFU Cache

The hard part is to remember to track a least global freq and note that it can ONLY
be reset on an insert or increase by 1 on an access.

**note** the lru semantics on eviction so even after LFU, for same key, eviction is by
LRU.

To do that in python without doing the whole LRU cache itself is to use `OrderedDict`.

```python
from collections import defaultdict, OrderedDict

class LFUCache:

    def __init__(self, capacity: int):
        self.cap = capacity
        self.g_mn = 0
        self.freq = {}
        self.with_freq = defaultdict(OrderedDict)
        self.store = {}

    def _touch(self, key: int):
        f = self.freq[key]

        del self.with_freq[f][key]

        if not self.with_freq[f]:
            del self.with_freq[f]
            if self.g_mn == f:
                self.g_mn += 1

        self.freq[key] = f + 1
        self.with_freq[f + 1][key] = None

    def get(self, key: int) -> int:
        if key not in self.store:
            return -1

        self._touch(key)
        return self.store[key]

    def put(self, key: int, value: int) -> None:
        if key in self.store:
            self._touch(key)
            self.store[key] = value
            return

        if len(self.store) == self.cap:
            evict_key, _ = self.with_freq[self.g_mn].popitem(last=False)

            if not self.with_freq[self.g_mn]:
                del self.with_freq[self.g_mn]

            del self.store[evict_key]
            del self.freq[evict_key]

        self.g_mn = 1
        self.freq[key] = 1
        self.with_freq[1][key] = None
        self.store[key] = value
```

It's best to just ask of the eviction order on same keys upfront rather than implementing
the arbitary eviction on same key first.

Changes needed to use `OrderedDict` as opposed to just a set of keys.

- note that technically all I need is anordered set but since we only have dict, we add
  keys with `None` as values
- So the set add becomes `self.with_freq[f + 1][key] = None`
- remove becomes a dict del `del self.with_freq[f][key]`
- pop is `evict_key, _ = self.with_freq[self.g_mn].popitem(last=False)`
  - that `_` value, here None

Why `last=False`,
internally it has the LRU item at head and MRU at last so last as False gives you the LRU
item.

```text
LRU                      MRU
 10   →   20   →   30
```
