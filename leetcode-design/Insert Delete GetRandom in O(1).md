# Insert Del Get Random

## No duplicated version ( Randomised Set )

Try to combine data structures, I need O(1) exists check, that's a set ( or rather map
here so you can just get index of it in the array ).
I need O(1) access for gettin random, so a list.
Deletion is a bit of a problem, as if for each elem if I start to store it's positions in the arrays, shifting will be problematic.

What if I don't shift instead find what index needs to be deleted, swap it with the end and
then just pop for O(1), that completes the solution.

```python
class RandomizedSet:

    def __init__(self):
        self.pos = {}
        self.elems = []

    def insert(self, val: int) -> bool:
        if val in self.pos:
            return False

        self.pos[val] = len(self.elems)
        self.elems.append(val)
        return True

    def remove(self, val: int) -> bool:
        if val not in self.pos:
            return False
        # idx to del and last copy
        idx = self.pos[val]
        last = self.elems[-1]
        # move last to idx
        self.elems[idx] = last
        self.pos[last] = idx
        # del
        self.elems.pop()
        del self.pos[val]

        return True

    def getRandom(self) -> int:
        return random.choice(self.elems)
```

## With duplicated ( Randomised Collection )

instead of just one index, you begin to store set of indices.
insert and get remain the same, for a remove, just assume you are removing the
last index for that val, and that completes the solution.

```python
class RandomizedCollection:

    def __init__(self):
        self.pos = {}
        self.elems = []

    def insert(self, val: int) -> bool:
        if val not in self.pos:
            self.pos[val] = set()

        self.pos[val].add(len(self.elems))
        self.elems.append(val)

        return len(self.pos[val]) == 1

    def remove(self, val: int) -> bool:
        if val not in self.pos:
            return False

        idx = self.pos[val].pop()
        last = self.elems[-1]

        if idx != len(self.elems) - 1:
            # move last from last index to idx
            self.elems[idx] = last
            self.pos[last].remove(len(self.elems) - 1)
            self.pos[last].add(idx)

        self.elems.pop()

        if not self.pos[val]:
            del self.pos[val]

        return True

    def getRandom(self) -> int:
        return random.choice(self.elems)
```

Focus on the remove, it's easy to get wrong, for this one the case on last
makes it really clean otherwise there are problems if you try to do it the
first way, problem being since you use sets, you need to be careful if you are
inserting a duplicate element into it, it'll be gone not appended; such an
approach would be fine for a list, but I would let's just use this casing evem
on the simpler solution, let's not try to be too clever here.
