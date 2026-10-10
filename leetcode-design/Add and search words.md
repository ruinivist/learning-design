# Add and search words

This is just a trie problme in disguise, not even in disguise.
Extra is jsut the "." based search so that is something.

Now two ways to handle the dot, one is to just dfs on every letter which seems to be intended given
there are at max 2 dots, so it cann't branch too much.

```python
class Node:
    def __init__(self):
        self.next = {}
        self.ends = False


class WordDictionary:

    def __init__(self):
        self.root = Node()

    def addWord(self, word: str) -> None:
        node = self.root
        for ch in word:
            if ch not in node.next:
                node.next[ch] = Node()
            node = node.next[ch]

        node.ends = True

    def search(self, word: str) -> bool:
        n = len(word)

        # note that node is the "prev" one, for example root is -1 index
        def f(pos, node):
            if pos == n:
                return node.ends

            ch = word[pos]
            if ch == ".":
                return any(f(pos + 1, nnode) for nnode in node.next.values())

            if ch in node.next:
                return f(pos + 1, node.next[ch])

            return False

        return f(0, self.root)
```

The only thing to note is the comment I made

- that node is the "prev" one, for example root is -1 index

This can explode exponentially if you have a LOT more dots but this is fine for the problem. Seems a generic
solution for those cases is to make something like pg's GIN.
