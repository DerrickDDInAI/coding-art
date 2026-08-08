"""A binary search tree that maps a brightness value to an image path.

What this is for
----------------
Photo-mosaic rendering asks the same question thousands of times: *"which of my
tile images best matches this small patch of the target photo?"*. The naive
answer compares the patch against every tile, so rendering a 100x100-cell mosaic
from 5 000 tiles costs 100 x 100 x 5 000 = 50 million comparisons.

If you reduce each tile to a single number — its mean brightness, say — the
question becomes "find the stored number closest to this one", and a binary
search tree answers that in about ``log2(n)`` steps instead of ``n``. For 5 000
tiles that is ~12 comparisons rather than 5 000: roughly 400x less work.

How a BST works
---------------
Every node holds one value. Everything in its **left** subtree is smaller,
everything in its **right** subtree is larger. So at each node you compare once
and discard half of the remaining candidates — the same idea as looking a word
up in a dictionary by opening it in the middle.

The catch: a BST is only fast when it is *balanced*. Insert already-sorted values
and every node ends up with an empty left side — the tree degenerates into a
linked list and lookups fall back to ``n`` steps. **Shuffle your values before
inserting them** (see ``build_tree`` below, which does it for you).

For production work, ``scipy.spatial.cKDTree`` does the same job in C and
generalises to multi-dimensional keys (matching on full RGB rather than a single
brightness value). This module is here to make the idea readable.
"""

# =====================================================================
# Import modules
# =====================================================================

# import internal modules
from random import shuffle
from typing import Any, List, Optional, Sequence, Tuple

# =====================================================================
# Define classes
# =====================================================================


class BSTNode:
    """One node of the tree: a value, an attached image path, and two children.

    Attributes:
    * val: the sortable key (e.g. the mean brightness of a tile).
    * img_path: the payload carried alongside the key.
    * left: subtree holding every value smaller than ``val``.
    * right: subtree holding every value larger than ``val``.
    """

    def __init__(self, val: Optional[Any] = None, img_path: Optional[str] = None) -> None:
        self.left: Optional["BSTNode"] = None
        self.right: Optional["BSTNode"] = None
        self.val = val
        self.img_path = img_path

    def __repr__(self) -> str:
        return f"BSTNode(val={self.val!r})"

    def insert(self, val: Any, img_path: Optional[str] = None) -> None:
        """Add a value, walking down until an empty slot is found.

        Duplicates are ignored: the tree stores one image per distinct value.
        """
        # an empty root node: fill it in rather than creating a child
        if self.val is None:
            self.val = val
            self.img_path = img_path
            return

        if self.val == val:
            return

        if val < self.val:
            if self.left:
                self.left.insert(val, img_path)
            else:
                self.left = BSTNode(val, img_path)
            return

        if self.right:
            self.right.insert(val, img_path)
        else:
            self.right = BSTNode(val, img_path)

    def get_min(self) -> Any:
        """Smallest value in the tree: keep going left until you cannot."""
        current = self
        while current.left is not None:
            current = current.left
        return current.val

    def get_max(self) -> Any:
        """Largest value in the tree: keep going right until you cannot."""
        current = self
        while current.right is not None:
            current = current.right
        return current.val

    def exists(self, val: Any) -> Tuple[bool, Any, Optional[str]]:
        """Look for an **exact** match.

        Returns ``(found, value, img_path)``. When there is no exact match, the
        value and path of the last node visited are returned — that node is a
        near miss, but *not* guaranteed to be the closest one in the tree. Use
        :meth:`find_closest` when you actually want the nearest neighbour, which
        is what mosaic matching needs.
        """
        if val == self.val:
            return True, self.val, self.img_path

        if val < self.val:
            if self.left is None:
                return False, self.val, self.img_path
            return self.left.exists(val)

        if self.right is None:
            return False, self.val, self.img_path
        return self.right.exists(val)

    def find_closest(self, val: Any) -> Tuple[Any, Optional[str]]:
        """Return the ``(value, img_path)`` whose value is nearest to ``val``.

        This is the operation a mosaic actually needs. Descending the tree can
        step *past* the best answer — the closest value may sit on the branch we
        just chose not to take — so we keep track of the best candidate seen so
        far while walking down, and return that rather than wherever we land.
        """
        current: Optional[BSTNode] = self
        best_node = self

        while current is not None:
            if abs(current.val - val) < abs(best_node.val - val):
                best_node = current

            # an exact hit cannot be improved on
            if val == current.val:
                break

            current = current.left if val < current.val else current.right

        return best_node.val, best_node.img_path

    def delete(self, val: Any) -> Optional["BSTNode"]:
        """Remove a value and return the new subtree root.

        Always reassign the result (``root = root.delete(x)``): deleting the root
        itself has to promote one of its children in its place.
        """
        if val < self.val:
            if self.left:
                self.left = self.left.delete(val)
            return self

        if val > self.val:
            if self.right:
                self.right = self.right.delete(val)
            return self

        # found it. With zero or one child, the child simply takes our place.
        if self.right is None:
            return self.left
        if self.left is None:
            return self.right

        # Two children: neither can be promoted directly without breaking the
        # ordering. Instead we copy in the *successor* — the smallest value on
        # the right — which is the only value that can sit here and keep every
        # left-smaller / right-larger relationship intact. Then we delete that
        # successor from the right subtree, where it is now a simpler case.
        min_larger_node = self.right
        while min_larger_node.left:
            min_larger_node = min_larger_node.left

        self.val = min_larger_node.val
        self.img_path = min_larger_node.img_path
        self.right = self.right.delete(min_larger_node.val)
        return self

    def preorder(self, vals: Optional[List[Any]] = None) -> List[Any]:
        """Node, then left, then right. Used to *copy* a tree: replaying a
        pre-order insertion rebuilds the identical shape."""
        vals = [] if vals is None else vals
        if self.val is not None:
            vals.append(self.val)
        if self.left is not None:
            self.left.preorder(vals)
        if self.right is not None:
            self.right.preorder(vals)
        return vals

    def inorder(self, vals: Optional[List[Any]] = None) -> List[Any]:
        """Left, then node, then right. This is the useful one: it returns the
        values in **sorted order**, which is a neat way to verify the tree is
        well-formed."""
        vals = [] if vals is None else vals
        if self.left is not None:
            self.left.inorder(vals)
        if self.val is not None:
            vals.append(self.val)
        if self.right is not None:
            self.right.inorder(vals)
        return vals

    def postorder(self, vals: Optional[List[Any]] = None) -> List[Any]:
        """Left, then right, then node. Children are always visited before their
        parent, which is what you want when freeing or aggregating a tree."""
        vals = [] if vals is None else vals
        if self.left is not None:
            self.left.postorder(vals)
        if self.right is not None:
            self.right.postorder(vals)
        if self.val is not None:
            vals.append(self.val)
        return vals


# =====================================================================
# Define functions
# =====================================================================


def build_tree(values: Sequence[Any], img_paths: Sequence[str], shuffle_first: bool = True) -> BSTNode:
    """Build a tree from parallel sequences of values and image paths.

    ``shuffle_first`` defaults to ``True`` on purpose: tile brightness values
    usually arrive sorted (because the image paths were sorted), and inserting
    sorted values builds a degenerate, linked-list-shaped tree with no speed
    benefit at all. Shuffling gives a tree that is balanced enough in practice.
    """
    if len(values) != len(img_paths):
        raise ValueError(f"values and img_paths must be the same length, got {len(values)} and {len(img_paths)}")

    if not values:
        raise ValueError("Cannot build a tree from an empty sequence.")

    pairs = list(zip(values, img_paths))

    if shuffle_first:
        shuffle(pairs)

    root = BSTNode(pairs[0][0], pairs[0][1])
    for val, img_path in pairs[1:]:
        root.insert(val, img_path)

    return root
