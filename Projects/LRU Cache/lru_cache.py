from abc import ABC, abstractmethod
from collections import defaultdict, deque
from collections.abc import Hashable
from dataclasses import dataclass
from typing import Any

# python has no linked list so we make one
# eq=False: nodes are positions, compare by identity so that two with same values are not same
@dataclass(slots=True, eq=False)
class Node:
    # ideally this should be generic on T but fine for now ig
    data: Any = None
    prev: "Node | None" = None
    next: "Node | None" = None

class DLList:
    def __init__(self):
        # single sentinel version
        self.root = Node()
        self.root.next = self.root.prev = self.root

    def delete(self, node: Node):
        node.prev.next, node.next.prev = node.next, node.prev

    # a "touch" would be delete and then a push front
    def push_front(self, node: Node):
        # link node
        node.prev, node.next = self.root, self.root.next
        # link root
        self.root.next.prev = node
        self.root.next = node

    # delete the most stale entry
    def pop_back(self) -> Node:
        last = self.root.prev
        self.delete(last)
        return last

# Cache
# owns storage as dic[K, V]
# - a get fetches from storage and notifies policy
# - a put
#   - already there: notices policy of access
#   - not there, if full ask of evict key, notify when evict done then insert and notify of insert
#
# In short policy holds the keys ( to enact the policy ) and is notified via the callbacks on insert
# evict and access

class EvictionPolicy[K](ABC):
    @abstractmethod
    def on_access(self, key: K) -> None: ...

    @abstractmethod
    def on_insert(self, key: K) -> None: ...

    @abstractmethod
    def evict(self) -> K: ...


# a problem with LRU? vulnerable to scans = a scan of keys where count of keys is larger than
# capacity clears all of the cache, the fix is something like SLRU
# SLRU keeps two LRUs, new keys start in a "probation" list and are only promoted to "protected" list
# on second hit so one time scans get evicted from probation without touching the main cache set

class LRU[K](EvictionPolicy[K]):
    # capacity is owned by the Cache, shouldn't be handled here
    def __init__(self):
        self.to_node: dict[K, Node] = {}
        self.list: DLList = DLList()

    def on_access(self, key: K):
        node = self.to_node[key]
        self.list.delete(node)
        self.list.push_front(node)

    def on_insert(self,key):
        node = Node(key)
        self.to_node[key] = node
        self.list.push_front(node)

    def evict(self) -> K:
        if not self.to_node:
            raise IndexError("nothing to evict")
        node = self.list.pop_back()
        del self.to_node[node.data]
        return node.data

class LFU[K](EvictionPolicy[K]):
    def __init__(self):
        self.min_freq = 0
        self.freqs: dict[K,int] = dict()
        self.with_freqs: dict[int, set[K]] = defaultdict(set)

    def on_access(self, key):
        f = self.freqs[key]
        self.with_freqs[f].remove(key)
        if not self.with_freqs[f] and self.min_freq == f:
            # freqs can only increase by 1
            self.min_freq += 1
        self.with_freqs[f+1].add(key)
        self.freqs[key] += 1

    def on_insert(self, key):
        self.freqs[key] = 1
        self.min_freq = 1
        self.with_freqs[1].add(key)

    def evict(self) -> K:
        # we don't reset the min_freq here, the policy here DEPENDS
        # on implicit assumption that an insert would be called after
        # an evict. Alternative is to keep two mins, but fine for now
        evict_key = self.with_freqs[self.min_freq].pop()
        del self.freqs[evict_key]
        return evict_key

# this one is trivial, you just need a deque; only adding for completeness
class FIFO[K](EvictionPolicy[K]):
    def __init__(self):
        self.q = deque()

    # only insert evict matters
    def on_access(self, key): ...

    def on_insert(self, key):
        self.q.append(key)

    def evict(self):
        return self.q.popleft()

class Cache[K: Hashable,V]:
    def __init__(self, capacity: int, policy:EvictionPolicy[K]):
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self.capacity: int = capacity
        self.store: dict[K,V] = {}
        self.policy = policy

    def get(self, key: K) -> V | None:
        if key not in self.store:
            return None
        self.policy.on_access(key)
        return self.store[key]

    def put(self, key: K, value: V) -> None:
        if key in self.store:
            self.policy.on_access(key)
            self.store[key] = value
            return

        if len(self.store)==self.capacity:
            evict_key = self.policy.evict()
            del self.store[evict_key]

        self.store[key] = value
        self.policy.on_insert(key)
