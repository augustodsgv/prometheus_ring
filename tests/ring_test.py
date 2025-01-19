import pytest
from prometheus_ring.ring import Ring, KeyAlreadyExistsError, KeyNotFoundError
from prometheus_ring.node import Node
from prometheus_ring.adt.abstract_data_type import AbstractDataType
from prometheus_ring.target import Target
from prometheus_ring.hash import hash

class MockADT(AbstractDataType):
    def __init__(self):
        self.data = {}

    def insert(self, key, value):
        self.data[key] = value

    def list(self):
        return list(self.data.values())

    def find_max_smaller_than(self, hash_value):
        keys = sorted(self.data.keys())
        for key in reversed(keys):
            if key < hash_value:
                return self.data[key]
        return self.data[keys[0]]

    def update(self, key, new_value):
        self.data[key] = new_value

    def search(self, key):
        return self.data.get(key)

    def remove(self, key):
        del self.data[key]

@pytest.fixture
def ring():
    adt = MockADT()
    return Ring(
        node_capacity=4,
        node_min_load=25,
        node_max_load=75,           # Scaling up at 75%
        sd_url='localhost',
        sd_port='9090',
        adt=adt
    )

def test_insert_target(ring):
    target = Target(id='1234', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    ring.insert(target, '1234')
    assert ring.get('1234') == target

def test_insert_duplicate_key(ring):
    target = Target(id='1234', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    ring.insert(target, '1234')
    with pytest.raises(KeyAlreadyExistsError):
        ring.insert(target, '1234')

def test_get_nonexistent_key(ring):
    with pytest.raises(KeyNotFoundError):
        ring.get('nonexistent')

def test_update_target(ring):
    target = Target(id='1234', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    ring.insert(target, '1234')
    new_target = Target(id='1234', name='t2', address='t2-address', metrics_port=9000, metrics_path='/metrics')
    ring.update('1234', new_target)
    assert ring.get('1234') == new_target

def test_delete_target(ring):
    target = Target(id='1234', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    ring.insert(target, '1234')
    ring.delete('1234')
    with pytest.raises(KeyNotFoundError):
        ring.get('1234')

def test_node_scaling_up(ring):
    target1 = Target(id='1234', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    target2 = Target(id='5678', name='t2', address='t2-address', metrics_port=8000, metrics_path='/metrics')
    target3 = Target(id='4321', name='t3', address='t3-address', metrics_port=8000, metrics_path='/metrics')
    target4 = Target(id='4321', name='t4', address='t4-address', metrics_port=8000, metrics_path='/metrics')
    assert ring.insert(target1, '1234') is None
    assert ring.insert(target2, '5678') is None
    assert ring.insert(target3, '4321') is not None       # Node scaling up
    assert ring.insert(target4, '8765') is None
    assert ring.get('1234') == target1
    assert ring.get('5678') == target2
    assert ring.get('4321') == target3
    assert ring.get('8765') == target4

def test_node_scaling_down_node_zero_last(ring):
    """
    During target deletion there is an edge case where the system may not scale down because the underloaded 
    node is the node_zero. In this test we will scale down the other node first
    """
    target1 = Target(id='1234', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    target2 = Target(id='5678', name='t2', address='t2-address', metrics_port=8000, metrics_path='/metrics')
    target3 = Target(id='4321', name='t3', address='t3-address', metrics_port=8000, metrics_path='/metrics')
    target4 = Target(id='8765', name='t4', address='t4-address', metrics_port=8000, metrics_path='/metrics')
    assert ring.insert(target1, '1234') is None
    assert ring.insert(target2, '5678') is None
    assert ring.insert(target3, '4321') is not None         # Node scaling up
    assert ring.insert(target4, '8765') is None

    all_targets_indexes = ['1234', '5678', '4321', '8765']
    node_zero_targets_indexes = [target.id for target in ring.node_zero.list_items()]
    other_node_targets_indexes = [target for target in all_targets_indexes if target not in node_zero_targets_indexes]
    # The first target removal will scale down the cluster
    removed_node = ring.delete(other_node_targets_indexes[0])
    assert removed_node is not None
    assert removed_node is not ring.node_zero
    # The second target is now in another node, so it will not scale down
    assert ring.delete(other_node_targets_indexes[1]) is None

    # The other targets are in the node_zero now, and ring should not scale down
    assert ring.delete(node_zero_targets_indexes[0]) is None
    assert ring.delete(node_zero_targets_indexes[1]) is None


def test_node_scaling_down_node_zero_first(ring):
    """
    During target deletion there is an edge case where the system may not scale down because the underloaded 
    node is the node_zero.
    In this test we will scale down the node zero and them the other node.
    In this case, the zero node will receive another target after the second node is removed
    """
    target1 = Target(id='1234', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    target2 = Target(id='5678', name='t2', address='t2-address', metrics_port=8000, metrics_path='/metrics')
    target3 = Target(id='4321', name='t3', address='t3-address', metrics_port=8000, metrics_path='/metrics')
    target4 = Target(id='8765', name='t4', address='t4-address', metrics_port=8000, metrics_path='/metrics')

    assert ring.insert(target1, '1234') is None
    assert ring.insert(target2, '5678') is None
    assert ring.insert(target3, '4321') is not None         # Node scaling up
    assert ring.insert(target4, '8765') is None

    all_targets_indexes = ['1234', '5678', '4321', '8765']
    node_zero_targets_indexes = [target.id for target in ring.node_zero.list_items()]
    other_node_targets_indexes = [target for target in all_targets_indexes if target not in node_zero_targets_indexes]

    removed_node = ring.delete(other_node_targets_indexes[0])
    assert removed_node is not None
    assert removed_node is not ring.node_zero
    # The second target of the other node was sent to node_zero, so node zero now should be almost overloaded
    assert ring.node_zero.load == 75

    # Removing all other nodes. Node zero should not be deleted, so all returns None
    assert ring.delete(other_node_targets_indexes[1]) is None
    assert ring.delete(node_zero_targets_indexes[0]) is None
    assert ring.delete(node_zero_targets_indexes[1]) is None

    # And finally node zero should have zero load
    assert ring.node_zero.load == 0