# Snapshot Array

Here we snapshot the whole of array, to make it simple these snaps are not time based so you don't
need that >= latest snap handling, exact snap ids work.

Now a trivial way is to store a full copy on each snap, a little smarter would be store a diff representation on the whole of array, but can we do any better?

Note that all they query on is the idx, so if the diff representation lives at the element level,
that makes it simpler.

Define an element to be a map where a value is stored for EACH id, there would a LOT of redundant
updates if we just naively store. Notice that the snap ids are inc, so borrow from the time idea
and make each element a list of (snap_id, val), then to get as of snap id you can bin search for
largest snap id <= the snap id being asked for, this way we've avoided duplicated entirely and this
naturally fits into the solution had the snap ids been timestamps, all we need is for them to be
increasing which they are.

Impl note:

- initially I made snap as O(n) but note that you are losing info, a repeated snap will still check
  everything. Instead do the snapping in set itself.
- But I also don't wanna store needless ids, so we COULD have a bending map of have inf as the pending
  snap ids but really, much cleaner to just have a pending map.

```python
class SnapshotArray:

    def __init__(self, length: int):
        self.snap_id = 0
        self.n = length
        self.arr = [[] for _ in range(length)]
        self.pending = {}

    def set(self, index: int, val: int) -> None:
        self.pending[index] = val

    def snap(self) -> int:
        sid, self.snap_id = self.snap_id, self.snap_id + 1
        for idx, val in self.pending.items():
            elems = self.arr[idx]
            if not elems or elems[-1][1] != val:
                elems.append((sid, val))
        self.pending.clear()
        return sid

    def get(self, index: int, snap_id: int) -> int:
        # need largest <= val
        snap_idx = bisect_right(self.arr[index], snap_id, key=lambda x: x[0]) - 1
        if snap_idx < 0:
            # init was all 0
            return 0
        return self.arr[index][snap_idx][1]
```
