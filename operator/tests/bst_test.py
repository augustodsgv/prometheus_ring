import pytest
import pytest_mock
from prometheus_ring.adt.binary_search_tree import BinarySearchTree

def test_insert_10_5_15():
    """
        10
      /    \\
    5       15 
    """
    bst = BinarySearchTree()
    bst.insert(10, "value10")
    bst.insert(5, "value5")
    bst.insert(15, "value15")
    assert bst.root.key == 10
    assert bst.root.left.key == 5
    assert bst.root.right.key == 15

def test_insert_20_10_5_15_30_25_35():
    """
                 20
              /      \\
             10        30
           /    \    /    \\
          5      15 25     35
    """
    bst = BinarySearchTree()
    bst.insert(20, "value20")
    bst.insert(10, "value10")
    bst.insert(5, "value5")
    bst.insert(15, "value15")
    bst.insert(30, "value30")
    bst.insert(25, "value25")
    bst.insert(35, "value35")

    assert bst.root.key == 20
    assert bst.root.left.key == 10
    assert bst.root.left.left.key == 5
    assert bst.root.left.right.key == 15
    assert bst.root.right.key == 30
    assert bst.root.right.left.key == 25
    assert bst.root.right.right.key == 35
    assert bst.search(20) == "value20"
    assert bst.search(10) == "value10"
    assert bst.search(5) == "value5"
    assert bst.search(15) == "value15"
    assert bst.search(30) == "value30"
    assert bst.search(25) == "value25"
    assert bst.search(35) == "value35"
    assert bst.search(26) is None

def test_search_10_5_15():
    """
        10
      /    \\
    5       15 
    """
    bst = BinarySearchTree()
    bst.insert(10, "value10")
    bst.insert(5, "value5")
    bst.insert(15, "value15")
    assert bst.search(10) == "value10"
    assert bst.search(5) == "value5"
    assert bst.search(15) == "value15"
    assert bst.search(20) is None

def test_update_10_5_15():
    bst = BinarySearchTree()
    bst.insert(10, "value10")
    bst.insert(5, "value5")
    bst.insert(15, "value15")
    old_value = bst.update(10, "new_value10")
    assert old_value == "value10"
    assert bst.search(10) == "new_value10"
    assert bst.update(20, "value20") is None

def test_inorder_10_5_15():
    bst = BinarySearchTree()
    bst.insert(10, "value10")
    bst.insert(5, "value5")
    bst.insert(15, "value15")
    assert bst.inorder() == [(5, "value5"), (10, "value10"), (15, "value15")]

def test_remove_10_5_15():
    bst = BinarySearchTree()
    bst.insert(10, "value10")
    bst.insert(5, "value5")
    bst.insert(15, "value15")
    bst.remove(10)
    assert bst.search(10) is None
    assert bst.root.key == 15
    assert bst.root.left.key == 5

def test_find_max_smaller_than_10_5_15():
    bst = BinarySearchTree()
    bst.insert(10, "value10")
    bst.insert(5, "value5")
    bst.insert(15, "value15")
    assert bst.find_max_smaller_than(15) == "value10"
    assert bst.find_max_smaller_than(10) == "value5"
    assert bst.find_max_smaller_than(5) == None

def test_find_min_greater_than():
    bst = BinarySearchTree()
    bst.insert(10, "value10")
    bst.insert(5, "value5")
    bst.insert(15, "value15")
    assert bst.find_min_greater_than(5) == "value10"
    assert bst.find_min_greater_than(10) == "value15"
    assert bst.find_min_greater_than(15) == None
