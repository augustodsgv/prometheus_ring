from typing import Any
from .abstract_data_type import AbstractDataType

class BSTNode:
    def __init__(self, key: int, value: Any):
        self.left = None
        self.right = None
        self.key = key
        self.value = value

class BinarySearchTree(AbstractDataType):
    def __init__(self):
        self.root: BSTNode | None = None
        
    def insert(self, key: int, value: Any):
        if self.root is None:
            self.root = BSTNode(key, value)
        else:
            self._insert(self.root, key, value)

    def _insert(self, root, key, value):
        if key < root.key:
            if root.left is None:
                root.left = BSTNode(key, value)
            else:
                self._insert(root.left, key, value)
        else:
            if root.right is None:
                root.right = BSTNode(key, value)
            else:
                self._insert(root.right, key, value)

    def search(self, key)-> Any | None:
        node = self._search(self.root, key)
        if node is None:
            return None
        return node.value

    def _search(self, root, key)->BSTNode:
        if root is None or root.key == key:
            return root
        
        if key < root.key:
            return self._search(root.left, key)
        
        return self._search(root.right, key)

    def update(self, key: int, new_value: Any)->Any | None:
        """
        Updates the node value, if found. Else, returns None
        """
        node = self._update(self.root, key)
        if node is None:
            return None
        old_value = node.value
        node.value = new_value
        return old_value
    
    def _update(self, root: BSTNode, key: int)->BSTNode:
        """
        Searches the value for the update operation
        """
        if root is None or root.key == key:
            return root
        
        if root.key < key:
            return self._update(root.right, key)
        
        return self._update(root.left, key)
    
    def inorder(self)->list[Any | None]:
        return self._inorder(self.root)
    
    def list(self)->list[Any]:
        return [node for key, node in self.inorder()]


    def _inorder(self, root):
        res = []
        if root:
            res = self._inorder(root.left)
            res.append((root.key, root.value))
            res = res + self._inorder(root.right)
        return res

    def print_tree(self):
        lines = self._build_tree_string(self.root, 0, False, '-')[0]
        for line in lines:
            print(line)

    def _build_tree_string(self, root, curr_index, include_index=False, delimiter='-'):
        if root is None:
            return [], 0, 0, 0

        line1 = []
        line2 = []
        if include_index:
            node_repr = '{}{}{}'.format(curr_index, delimiter, root.key)
        else:
            node_repr = str(root.key)

        new_root_width = gap_size = len(node_repr)

        # Get the left and right sub-boxes, their widths, and root repr positions
        l_box, l_box_width, l_root_start, l_root_end = self._build_tree_string(root.left, 2 * curr_index + 1, include_index, delimiter)
        r_box, r_box_width, r_root_start, r_root_end = self._build_tree_string(root.right, 2 * curr_index + 2, include_index, delimiter)

        # Draw the branch connecting the current root node to the left sub-box
        if l_box_width > 0:
            l_root = (l_root_start + l_root_end) // 2 + 1
            line1.append(' ' * (l_root + 1))
            line1.append('_' * (l_box_width - l_root))
            line2.append(' ' * l_root + '/')
            line2.append(' ' * (l_box_width - l_root))
            new_root_start = l_box_width + 1
            gap_size += 1
        else:
            new_root_start = 0

        # Draw the representation of the current root node
        line1.append(node_repr)
        line2.append(' ' * new_root_width)

        # Draw the branch connecting the current root node to the right sub-box
        if r_box_width > 0:
            r_root = (r_root_start + r_root_end) // 2
            line1.append('_' * r_root)
            line1.append(' ' * (r_box_width - r_root + 1))
            line2.append(' ' * r_root + '\\')
            line2.append(' ' * (r_box_width - r_root))
            gap_size += 1
        new_root_end = new_root_start + new_root_width - 1

        # Combine the left and right sub-boxes with the branches
        gap = ' ' * gap_size
        new_box = [''.join(line1), ''.join(line2)]
        for i in range(max(len(l_box), len(r_box))):
            l_line = l_box[i] if i < len(l_box) else ' ' * l_box_width
            r_line = r_box[i] if i < len(r_box) else ' ' * r_box_width
            new_box.append(l_line + gap + r_line)

        return new_box, len(new_box[0]), new_root_start, new_root_end

    def remove(self, key: str)->BSTNode | None:
        return self._remove(self.root, key)

    def _remove(self, root, key):
        if root is None:
            return root

        if root.key > key:
            root.left = self._remove(root.left, key)

        elif root.key < key:
            root.right = self._remove(root.right, key)
        else:
            if root.left is None:
                return root.right
            elif root.right is None:
                return root.left

            temp = self._min_key_node(root.right)
            root.key = temp.key
            root.right = self._remove(root.right, temp.key)

        return root

    def _min_key_node(self, node):
        current = node
        while current.left is not None:
            current = current.left
        return current
    
    def find_max_smaller_than(self, key: int)->Any:
        """
        Returns any value that was stored in this node
        WARN: this is problably a bad name for it, but nevermind
        """
        node = self._find_max_smaller_than(self.root, key, None)
        if node is None:
            return None
        return node.value

    def _find_max_smaller_than(self, root, key: int, max_node)->BSTNode:
        if root is None:
            return max_node

        # if root.key == key:         # If is the node, 
        #     return root
        if root.key < key:          # If root is less than key: we can try to go right and increase our node key
            max_node = root
            return self._find_max_smaller_than(root.right, key, max_node)
        else:                 
                  # If root is greater, we can only go try to get an node with smaller number
            return self._find_max_smaller_than(root.left, key, max_node)
        
    def find_min_greater_than(self, key: int)->Any:
        """
        Returns any value that was stored in this node
        """
        node = self._find_min_greater_than(self.root, key, None)
        if node is None:
            return None
        return node.value

    def _find_min_greater_than(self, root, key: int, max_node)->BSTNode:
        if root is None:
            return max_node
        
        # if root.key == key:
        #     return key

        if root.key > key:          # If root is greater than key: int, we can try to go left and decreate our node key
            max_node = root
            return self._find_min_greater_than(root.left, key, max_node)
        
        else:                       # If root is less, we can only go try to get an node with a greater number
            return self._find_min_greater_than(root.right, key, max_node)
