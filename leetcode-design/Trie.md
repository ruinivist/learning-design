# Trie

Just a word trie for a prefix contains and and exact contains search.
You would basically want to store count of ends at any node, this will give you an easy exact match.
For prefix, you can of course descent all trees once you match a prefix and count if there are any ends
or have it computed as sum of ends in this and below when you insert.
For a clever impl for this specific problem which does not delete anything, if ANY child path exists
then you have a prefix.

```python
class Node:
    def __init__(self):
        self.next = {}
        self.ends = 0


class Trie:

    def __init__(self):
        self.root = Node()

    def _travel(self, word, create) -> Node | None:
        root = self.root
        for ch in word:
            if ch not in root.next:
                if not create:
                    return None
                root.next[ch] = Node()

            root = root.next[ch]
        return root

    def insert(self, word: str) -> None:
        node = self._travel(word, True)
        node.ends += 1

    def search(self, word: str) -> bool:
        node = self._travel(word, False)
        return node is not None and node.ends > 0

    def startsWith(self, prefix: str) -> bool:
        return self._travel(prefix, False) is not None
```
