# LRU Cache

Nothing to write since I've done this problem so so so many times.

```python
from dataclasses import dataclass


@dataclass(slots=True, eq=False)
class Node:
    key: int = None
    val: int = None
    next: Node = None
    prev: Node = None


class DLList:
    def __init__(self):
        self.root = Node()
        self.root.next, self.root.prev = self.root, self.root

    def delete(self, node):
        node.prev.next, node.next.prev = node.next, node.prev

    def pushFront(self, node):
        # first join node
        node.next = self.root.next
        node.prev = self.root
        # update rest
        self.root.next.prev = node
        self.root.next = node

    def popBack(self):
        last = self.root.prev
        self.delete(last)
        return last


class LRUCache:

    def __init__(self, capacity: int):
        self.n = capacity
        self.to_node = {}
        self.list = DLList()

    def get(self, key: int) -> int:
        if key not in self.to_node:
            return -1

        node = self.to_node[key]
        self.list.delete(node)
        self.list.pushFront(node)
        return node.val

    def put(self, key: int, value: int) -> None:
        if key in self.to_node:
            node = self.to_node[key]
            node.val = value
            self.list.delete(node)
            self.list.pushFront(node)
            return

        if len(self.to_node) == self.n:
            evict = self.list.popBack()
            del self.to_node[evict.key]

        node = Node(key, value)
        self.to_node[key] = node
        self.list.pushFront(node)

```
