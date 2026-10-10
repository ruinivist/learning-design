# Serialize and deserialize bin tree

The idea is that you can use any format you like as long as you can reverse it.
A preorder traversal is reversible and easy so I use that.

To reverse, you do exacly how you would do the preorder.

```python
# Definition for a binary tree node.
# class TreeNode(object):
#     def __init__(self, x):
#         self.val = x
#         self.left = None
#         self.right = None


class Codec:

    def serialize(self, root):
        res = []

        def f(node):
            if not node:
                res.append("|")
                return

            res.append(str(node.val))
            f(node.left)
            f(node.right)

        f(root)
        return ",".join(res)

    def deserialize(self, data):
        vals = iter(data.split(","))

        def f():
            val = next(vals)

            if val == "|":
                return None

            node = TreeNode(int(val))
            node.left = f()
            node.right = f()
            return node

        return f()
```

The deserialize reversal is just a loop on the pre-order such that you handle the non
balanced nature by returning early.
