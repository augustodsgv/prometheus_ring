import pytest
import pytest_mock
from prometheus_ring.ring import Ring, KeyAlreadyExistsError, KeyNotFoundError
from prometheus_ring.node import Node
from prometheus_ring.adt.abstract_data_type import AbstractDataType
from prometheus_ring.target import Target
from prometheus_ring.hash import stable_hash


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
            if key <= hash_value:
                return self.data[key]
        return self.data[keys[0]]

    def update(self, key, new_value):
        self.data[key] = new_value

    def search(self, key):
        return self.data.get(key)

    def remove(self, key):
        del self.data[key]

@pytest.fixture
def ring_4():
    adt = MockADT()
    return Ring(
        node_capacity=4,
        node_min_load=25,
        node_max_load=75,           # Scaling up at 75%
        sd_url='localhost',
        sd_port='9090',
        adt=adt
    )

@pytest.fixture
def ring_5():
    adt = MockADT()
    return Ring(
        node_capacity=5,
        node_min_load=25,
        node_max_load=75,           # Scaling up at 75%
        sd_url='localhost',
        sd_port='9090',
        adt=adt
    )

def test_insert_target(ring_4):
    target = Target(id='1234', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    ring_4.insert(target, '1234')
    assert ring_4.get('1234') == target

def test_insert_duplicate_key(ring_4):
    target = Target(id='1234', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    ring_4.insert(target, '1234')
    with pytest.raises(KeyAlreadyExistsError):
        ring_4.insert(target, '1234')

def test_get_nonexistent_key(ring_4):
    with pytest.raises(KeyNotFoundError):
        ring_4.get('nonexistent')

def test_update_target(ring_4):
    target = Target(id='1234', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    ring_4.insert(target, '1234')
    new_target = Target(id='1234', name='t2', address='t2-address', metrics_port=9000, metrics_path='/metrics')
    ring_4.update('1234', new_target)
    assert ring_4.get('1234') == new_target

def test_delete_target(ring_4):
    target = Target(id='1234', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    ring_4.insert(target, '1234')
    ring_4.delete('1234')
    with pytest.raises(KeyNotFoundError):
        ring_4.get('1234')

def test_node_scaling_up(ring_4, mocker):
    """
    x. []
    0. (0)[1234]
    1. (0)[1234, 5678]
    2. (0)[1234, 5678, 4321]
    3. (0)[1234, 5678, 4321, 8765]--(split)-->(0)[1234, 4321], (4999)[5678, 8765]
    """
    mocker.patch('prometheus_ring.ring.stable_hash', side_effect=lambda x: int(x))
    mocker.patch('prometheus_ring.node.stable_hash', side_effect=lambda x: int(x))
    target1 = Target(id='1234', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    target2 = Target(id='5678', name='t2', address='t2-address', metrics_port=8000, metrics_path='/metrics')
    target3 = Target(id='4321', name='t3', address='t3-address', metrics_port=8000, metrics_path='/metrics')
    target4 = Target(id='8765', name='t4', address='t4-address', metrics_port=8000, metrics_path='/metrics')
    assert ring_4.insert(target1, '1234') is None
    assert ring_4.insert(target2, '5678') is None
    assert ring_4.insert(target3, '4321') is None
    new_node = ring_4.insert(target4, '8765')           # Node scaling up
    assert new_node is not None         
    assert new_node.index == 4999
    assert ring_4.get('1234') == target1
    assert ring_4.get('5678') == target2
    assert ring_4.get('4321') == target3
    assert ring_4.get('8765') == target4

def test_scaling_down_node_zero_last(ring_4, mocker):
    """
    During target deletion there is an edge case where the system may not scale down because the underloaded 
    node is the node_zero. In this test we will scale down the other node first
    x. [0, 1], [3, 4]
    0. [0, 1], [3]--(merge)-->[0, 1, 3]
    1. [0, 1]
    2. [0]                          # Does not scale down because is node zero
    3. []                           # Does not delete node because is node zero

    """
    mocker.patch('prometheus_ring.ring.stable_hash', side_effect=lambda x: int(x))
    mocker.patch('prometheus_ring.node.stable_hash', side_effect=lambda x: int(x))

    target1 = Target(id='0', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    target2 = Target(id='1', name='t2', address='t2-address', metrics_port=8000, metrics_path='/metrics')
    target3 = Target(id='3', name='t3', address='t3-address', metrics_port=8000, metrics_path='/metrics')
    target4 = Target(id='4', name='t4', address='t4-address', metrics_port=8000, metrics_path='/metrics')
    assert ring_4.insert(target1, '0') is None
    assert ring_4.insert(target2, '1') is None
    assert ring_4.insert(target3, '3') is None
    new_node =  ring_4.insert(target4, '4')          # Node scaling up
    assert new_node is not None
    assert new_node.index == 2
    
    # The first target removal will scale down the cluster
    removed_node = ring_4.delete('4')
    assert removed_node is not None
    assert removed_node is not ring_4.node_zero
    # The second target is now in another node, so it will not scale down
    assert ring_4.delete('3') is None

    # The other targets are in the node_zero now, and ring should not scale down
    assert ring_4.delete('1') is None
    assert ring_4.delete('0') is None


def test_scaling_down_node_zero_first(ring_4, mocker):
    """
    During target deletion there is an edge case where the system may not scale down because the underloaded 
    node is the node_zero.
    In this test we will scale down the node zero and them the other node.
    In this case, the zero node will receive another target after the second node is removed
    x. (0)[500, 5000, 50000], (138875)[500000]
    0. (0)[5000, 50000], (138875)[500000]                       # Does not scale down
    1. (0)[50000], (138875)[500000]
    2. (0)[] (138875)[50000]--(merge)-->(0)[]             # scales down
    """
    mocker.patch('prometheus_ring.ring.stable_hash', side_effect=lambda x: int(x))
    mocker.patch('prometheus_ring.node.stable_hash', side_effect=lambda x: int(x))
    
    target1 = Target(id='500', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    target2 = Target(id='5000', name='t2', address='t2-address', metrics_port=8000, metrics_path='/metrics')
    target3 = Target(id='50000', name='t3', address='t3-address', metrics_port=8000, metrics_path='/metrics')
    target4 = Target(id='500000', name='t4', address='t4-address', metrics_port=8000, metrics_path='/metrics')

    assert ring_4.insert(target1, '500') is None
    assert ring_4.insert(target2, '5000') is None
    assert ring_4.insert(target3, '50000') is None         # Node scaling up
    assert ring_4.insert(target4, '500000') is not None
    print(ring_4.get_nodes())

    assert ring_4.delete('500') is None
    assert ring_4.node_zero.load == 50
    print(ring_4.get_nodes())
    assert ring_4.delete('5000') is None
    assert ring_4.node_zero.load == 25
    print(ring_4.get_nodes())

    # Removing all other targets. Node zero should not be deleted, so all returns None
    assert ring_4.delete('50000') is None
    deleted_node =  ring_4.delete('500000')
    assert deleted_node is not None
    assert deleted_node.index == 138875
    assert ring_4.node_zero.load == 0

def test_insertion_many_targets_in_order(ring_4, mocker):
    """
    It's impossible to determine the exacly behavior of the ring because of the use of the hash.
    We can test, however, some specific cases and assume that the other are ok
    This functions tests the ordered hash insertion, which is the worst case scenario
    After the first split, only the last node will scale up. So, after the 3rd insertion,
    each two insertions will split a node
    
    For example
    x. (0)[]
    0. (0)[0]
    1. (0)[0, 10]
    2. (0)[0, 10, 20]                 # Its equal, not greater, so wont split
    3. (0)[0, 10, 20, 30]--(split)-->(0)[0, 10], (15)[20, 30]
    4. (0)[0, 10], (15)[20, 30, 40]
    5. (0)[0, 10], (15)[20, 30, 40, 50]--(split)-->(0)[0, 10], (15)[2, 3], (35)[40, 50]
    6. (0)[0, 1], (15)[20, 30], (35)[40, 50, 60]
    7. (0)[0, 1], (15)[20, 30], (35)[40, 50, 60, 70]--(split)-->(0)[0, 10], (15)[20, 30], (35)[40, 50], (55)[60, 70]
    8. (0)[0, 1], (15)[20, 30], (35)[40, 50], (55)[60, 70, 80]
    9. (0)[0, 1], (15)[20, 30], (35)[40, 50], (65)[60, 70, 80, 90]--(split)-->(0)[0, 10], (15)[20, 30], (35)[40, 50], (55)[60, 70], (75)[80, 90]
    """
    mocker.patch('prometheus_ring.ring.stable_hash', side_effect=lambda x: int(x))
    mocker.patch('prometheus_ring.node.stable_hash', side_effect=lambda x: int(x))
    target_list = list()
    for i in range(0, 100, 10):
        new_target = Target(id=str(i), name=f't-{i}', address=f't{i}-address', metrics_port=8000, metrics_path='/metrics')
        target_list.append(new_target)
    # Once hash is an one-way function, neet to keep track of it

    # Inserting the first target so we can simplificate the loop
    assert ring_4.insert(target_list[0], target_list[0].id) is None
    assert ring_4.insert(target_list[1], target_list[1].id) is None
    assert ring_4.insert(target_list[2], target_list[2].id) is None
    assert ring_4.insert(target_list[3], target_list[3].id) is not None
    assert ring_4.insert(target_list[4], target_list[4].id) is None
    assert ring_4.insert(target_list[5], target_list[5].id) is not None
    assert ring_4.insert(target_list[6], target_list[6].id) is None
    assert ring_4.insert(target_list[7], target_list[7].id) is not None
    assert ring_4.insert(target_list[8], target_list[8].id) is None
    assert ring_4.insert(target_list[9], target_list[9].id) is not None

def test_insertion_many_targets_in_order_discrepant_elements(ring_4, mocker):
    """
    It's impossible to determine the exact behavior of the ring because of the use of the hash.
    We can test, however, some specific cases and assume that the other are ok.
    This function tests the ordered hash insertion, which is the worst-case scenario.
    After the first split, only the last node will scale up. So, after the 3rd insertion,
    each two insertions will split a node.
    
    For example:
    x. []
    0. [0]
    1. [0, 100]
    2. [0, 100, 200]                 # It's equal, not greater, so won't split
    3. [0, 100, 200, 300]--(split)-->[0, 100], [200, 300]
    4. [0, 100], [200, 300, 400]
    5. [0, 100], [200, 300, 400, 500]--(split)-->[0, 100], [200, 300], [400, 500]
    6. [0, 100], [200, 300], [400, 500, 600]
    7. [0, 100], [200, 300], [400, 500, 600, 700]--(split)-->[0, 100], [200, 300], [400, 500], [600, 700]
    8. [0, 100], [200, 300], [400, 500], [600, 700, 800]
    9. [0, 100], [200, 300], [400, 500], [600, 700, 800, 900]--(split)-->[0, 100], [200, 300], [400, 500], [600, 700], [800, 900]
    """
    mocker.patch('prometheus_ring.ring.stable_hash', side_effect=lambda x: int(x))
    target_list = list()
    for i in range(0, 1000, 100):
        new_target = Target(id=str(i), name=f't-{i}', address=f't{i}-address', metrics_port=8000, metrics_path='/metrics')
        target_list.append(new_target)
    # Once hash is an one-way function, neet to keep track of it

    # Inserting the first target so we can simplificate the loop
    assert ring_4.insert(target_list[0], target_list[0].id) is None
    assert ring_4.insert(target_list[1], target_list[1].id) is None
    assert ring_4.insert(target_list[2], target_list[2].id) is None
    assert ring_4.insert(target_list[3], target_list[3].id) is not None
    assert ring_4.insert(target_list[4], target_list[4].id) is None
    assert ring_4.insert(target_list[5], target_list[5].id) is not None
    assert ring_4.insert(target_list[6], target_list[6].id) is None
    assert ring_4.insert(target_list[7], target_list[7].id) is not None
    assert ring_4.insert(target_list[8], target_list[8].id) is None
    assert ring_4.insert(target_list[9], target_list[9].id) is not None

def test_deletion_many_targets_in_order(ring_4, mocker):
    """
    This functions tests the ordered hash deletion, which is the worst case scenario (just as last test)
    
    For example
    x. [0, 10], [20, 30], [40, 50], [60, 70], [80, 90]
    0. [0, 10], [20, 30], [40, 50], [60, 70], [80]--(merge)-->[0, 10], [20, 30], [40, 50], [60, 70, 80]
    1. [0, 10], [20, 30], [40, 50], [60, 70]
    2. [0, 10], [20, 30], [40, 50], [60]--(merge)-->[0, 10], [20, 30], [40, 50, 60]
    3. [0, 10], [20, 30], [40, 50]
    4. [0, 10], [20, 30], [40]--(merge)-->[0, 10], [20, 30, 40]
    5. [0, 10], [20, 30]
    6. [0, 10], [20]--(merge)-->[0, 10, 20]
    7. [0, 10]
    8. [0]                                                                  # it should not merge, once it's only node zero left
    9. []
    """
    mocker.patch('prometheus_ring.ring.stable_hash', side_effect=lambda x: int(x))
    mocker.patch('prometheus_ring.node.stable_hash', side_effect=lambda x: int(x))
    target_list = list()
    for i in range(0, 100, 10):
        new_target = Target(id=str(i), name=f't{i}', address=f't{i}-address', metrics_port=8000, metrics_path='/metrics')
        target_list.append(new_target)
    # Once hash is an one-way function, neet to keep track of it
    
    for target in target_list:
        ring_4.insert(target, target.id)
    assert ring_4.delete('90') is not None
    assert ring_4.delete('80') is None
    assert ring_4.delete('70') is not None
    assert ring_4.delete('60') is None
    assert ring_4.delete('50') is not None
    assert ring_4.delete('40') is None
    assert ring_4.delete('30') is not None
    assert ring_4.delete('20') is None
    assert ring_4.delete('10') is None
    assert ring_4.delete('0') is None


def test_many_targets_in_order_capacity_5_threshold_25_75():
    """
    take node capacity = 5
    0.75 * 5 = 3.75. So it will expand each 4 * n insertions
    Now, for nodes with even number, that's the behavior
    (node_capacity * n) - 1 insertion.
    For example
    0. []
    1. [0]
    2. [0, 1]
    3. [0, 1, 2]
    4. [0, 1, 2, 3]--(split)-->[0, 1], [2, 3]
    5. [0, 1], [2, 3, 4]
    6. [0, 1], [2, 3, 4, 5]--(split)-->[0, 1], [2, 3], [4, 5]
    7. [0, 1], [2, 3], [4, 5, 6]
    8. [0, 1], [2, 3], [4, 5, 6, 7]--(split)-->[0, 1], [2, 3], [4, 5], [6, 7]
    and so on
    """

def test_many_targets_in_order_capacity_6_threshold_25_75():
    """
    take node capacity = 6
    0.75 * 6 = 4.5. So it will expand each 4 * n insertions
    Now, for nodes with even number, that's the behavior
    (node_capacity * n) - 1 insertion.
    For example
    0. []
    1. [0]
    2. [0, 1]
    3. [0, 1, 2]
    4. [0, 1, 2, 3]
    5. [0, 1, 2, 3, 4]--(split)-->[0, 1], [2, 3, 4]                                     # mean is 2.5 is floored to 2
    6. [0, 1], [2, 3, 4, 5]
    7. [0, 1], [2, 3, 4, 5, 6]--(split)-->[0, 1], [2, 3], [4, 5, 6]                     # mean = 4
    8. [0, 1], [2, 3], [4, 5, 6, 7]
    9. [0, 1], [2, 3], [4, 5, 6, 7, 8]--(split)-->[0, 1], [2, 3], [4, 5], [6, 7, 8]     # mean = 6
    and so on
    """
    ...

def test_many_targets_in_order_capacity_7_threshold_25_75():
    """
    take node capacity = 7
    0.75 * 7 = 5.25. 
    For example
    0. []
    1. [0]
    2. [0, 1]
    3. [0, 1, 2]
    4. [0, 1, 2, 3]
    5. [0, 1, 2, 3, 4]
    6. [0, 1, 2, 3, 4, 5]--(split)-->[0, 1, 2], [3, 4, 5]               # mean = 3
    7. [0, 1, 2], [3, 4, 5, 6]
    8. [0, 1, 2], [3, 4, 5, 6, 7]
    9. [0, 1, 2], [3, 4, 5, 6, 7, 8]--(split)-->[0, 1, 2], [3, 4, 5], [6, 7, 8] # mean = 6
    and so on
    """
    ...

def test_many_targets_in_order_capacity_8_threshold_25_75():
    """
    take node capacity = 8
    0.75 * 8 = 6. 
    For example
    0. []
    1. [0]
    2. [0, 1]
    3. [0, 1, 2]
    4. [0, 1, 2, 3]
    5. [0, 1, 2, 3, 4]
    6. [0, 1, 2, 3, 4, 5]--(split)-->[0, 1, 2], [3, 4, 5]               # mean = 3
    7. [0, 1, 2], [3, 4, 5, 6]
    8. [0, 1, 2], [3, 4, 5, 6, 7]
    9. [0, 1, 2], [3, 4, 5, 6, 7, 8]--(split)-->[0, 1, 2], [3, 4, 5], [6, 7, 8] # mean = 6
    and so on
    """
    ...

def test_insertion_many_targets_binary_by_halfs(ring_4, mocker):
    """
    Inserting nodes by halfs, switching from less and more than 8 alternating
    x. []
    0. (0)[0]
    1. (0)[0, 1024]
    2. (0)[0, 1024]
    """
    # mocker.patch('prometheus_ring.ring.stable_hash', side_effect=lambda x: int(x))
    # mocker.patch('prometheus_ring.node.stable_hash', side_effect=lambda x: int(x))
    # target_list = list()
    # for i in range(16):
    #     new_target = Target(id=str(i), name=f't-{i}', address=f't{i}-address', metrics_port=8000, metrics_path='/metrics')
    #     target_list.append(new_target)
    # # Once hash is an one-way function, neet to keep track of it

    # # Inserting the first target so we can simplificate the loop
    # assert ring_4.insert(target_list[0], '0') is None
    # assert ring_4.insert(target_list[8], '8') is None
    # assert ring_4.insert(target_list[1], '1') is None
    # assert ring_4.insert(target_list[9], '9').index == 5
    # print(ring_4.get_nodes())
    # assert ring_4.insert(target_list[2], '2') is None
    # assert ring_4.insert(target_list[10], '10') is None
    # assert ring_4.insert(target_list[3], '3').index == 2
    # print(ring_4.get_nodes())
    # assert ring_4.insert(target_list[11], '11').index == 10
    # print(ring_4.get_nodes())

    # assert ring_4.insert(target_list[4], '4') is None
    # assert ring_4.insert(target_list[12], '12') is None
    # print(ring_4.get_nodes())
    # assert ring_4.insert(target_list[5], '5') is None
    # assert ring_4.insert(target_list[13], '13').index == 12
    # assert ring_4.insert(target_list[6], '6').index == 8
    # assert ring_4.insert(target_list[14], '14') is None
    # assert ring_4.insert(target_list[7], '7') is None
    # assert ring_4.insert(target_list[15], '15').index == 14
    ...