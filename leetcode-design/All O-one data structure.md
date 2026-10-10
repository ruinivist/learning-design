# All O-one data structure

It's a freq counter with small string keys and support for getting the min and max
freq keys.

## Solution

I can use the LFU idea of min or max freqs only changing by one in each step to keep
track of the global min and max frequencies. We don't have a delete so the problem
of arbitrary jumps is just not there.

**problem** that I missed with this solution is that on a decreemnt while the idea
would work for a max but not for a min because are indeed getting deleted when freq
becomes 0 ( I missed this as keys not getting deleted at all ), for that case you
would need to jump to the next freq bucket.

Can we use ordered dict? It preserves insertion order, I want numeric sorder.
sorted dict exists as well with numeric order but it won't be O(1).

Way it to reuse the same idea as LRU cache but change it so that numerical order is
respected. Basically you define frequency buckets as nodes of the linked list, so
that traversing gives me the keys that are there in `with_freq` in a sorted order.
Naturally I would need a map from freq -> Node as well.

Or rather, just hold the set itself in nodes, so just a freq to bucket is all that's
needed ( apart from the rest of the things ).

```python
class Node:
    def __init__(self, count=0):
        self.count = count
        self.keys = set()
        self.prev = self.next = None


class DLList:
    def __init__(self):
        self.root = Node()
        self.root.prev = self.root.next = self.root

    def insert_after(self, node, count):
        new_node = Node(count)

        new_node.prev = node
        new_node.next = node.next

        node.next.prev = new_node
        node.next = new_node

        return new_node

    def remove(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev

    def first(self):
        return self.root.next

    def last(self):
        return self.root.prev

    def is_empty(self):
        return self.root.next is self.root


class AllOne:
    def __init__(self):
        self.freq = {}  # key -> frequency
        self.with_freq = {}  # frequency -> Node
        self.dll = DLList()

    def _insert_after(self, node, count):
        new_node = self.dll.insert_after(node, count)
        self.with_freq[count] = new_node
        return new_node

    def _remove(self, node):
        self.dll.remove(node)
        del self.with_freq[node.count]

    def inc(self, key: str) -> None:
        old_freq = self.freq.get(key, 0)
        new_freq = old_freq + 1

        # For a new key, start at the sentinel
        curr = self.with_freq[old_freq] if old_freq else self.dll.root
        nxt = curr.next

        # Find or create the new frequency node
        if nxt.count != new_freq:
            nxt = self._insert_after(curr, new_freq)

        # Add key to its new frequency
        nxt.keys.add(key)
        self.freq[key] = new_freq

        # Remove key from its old frequency
        if old_freq > 0:
            curr.keys.remove(key)

            if not curr.keys:
                self._remove(curr)

    def dec(self, key: str) -> None:
        old_freq = self.freq[key]
        new_freq = old_freq - 1

        curr = self.with_freq[old_freq]

        # Frequency 0 means the key is deleted
        if new_freq == 0:
            del self.freq[key]
        else:
            prev = curr.prev

            # Find or create the new frequency node
            if prev.count != new_freq:
                prev = self._insert_after(prev, new_freq)

            # Add key to its new frequency
            prev.keys.add(key)
            self.freq[key] = new_freq

        # Remove key from its old frequency
        curr.keys.remove(key)

        if not curr.keys:
            self._remove(curr)

    def getMaxKey(self) -> str:
        if self.dll.is_empty():
            return ""

        return next(iter(self.dll.last().keys))

    def getMinKey(self) -> str:
        if self.dll.is_empty():
            return ""

        return next(iter(self.dll.first().keys))
```

> This would be hard problem to do without any prior idea, I should review this one
> time and again
