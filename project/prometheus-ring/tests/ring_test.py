import pytest
import pytest_mock
from prometheus_ring.ring import Ring, KeyAlreadyExistsError, KeyNotFoundError
from prometheus_ring.node import Node
from prometheus_ring.adt.abstract_data_type import AbstractDataType
from prometheus_ring.adt.binary_search_tree import BinarySearchTree
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
            if key < hash_value:
                return self.data[key]
            
        return None

    def update(self, key, new_value):
        self.data[key] = new_value

    def search(self, key):
        return self.data.get(key)

    def remove(self, key):
        del self.data[key]

@pytest.fixture
def ring_mock_adt():
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
def ring_bst():
    return Ring(
        node_capacity=4,
        node_min_load=25,
        node_max_load=75,           # Scaling up at 75%
        sd_url='localhost',
        sd_port='9090',
        adt=BinarySearchTree()
    )

class TestMockAdt:
    def test_insert_target(self, ring_mock_adt):
        target = Target(id='1234', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
        ring_mock_adt.insert(target, '1234')
        assert ring_mock_adt.get('1234') == target

    def test_insert_duplicate_key(self, ring_mock_adt):
        target = Target(id='1234', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
        ring_mock_adt.insert(target, '1234')
        with pytest.raises(KeyAlreadyExistsError):
            ring_mock_adt.insert(target, '1234')

    def test_get_nonexistent_key(self, ring_mock_adt):
        with pytest.raises(KeyNotFoundError):
            ring_mock_adt.get('nonexistent')

    def test_update_target(self, ring_mock_adt):
        target = Target(id='1234', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
        ring_mock_adt.insert(target, '1234')
        new_target = Target(id='1234', name='t2', address='t2-address', metrics_port=9000, metrics_path='/metrics')
        ring_mock_adt.update('1234', new_target)
        assert ring_mock_adt.get('1234') == new_target

    def test_delete_target(self, ring_mock_adt):
        target = Target(id='1234', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
        ring_mock_adt.insert(target, '1234')
        ring_mock_adt.delete('1234')
        with pytest.raises(KeyNotFoundError):
            ring_mock_adt.get('1234')

    def test_node_scaling_up(self, ring_mock_adt, mocker):
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
        assert ring_mock_adt.insert(target1, '1234') is None
        assert ring_mock_adt.insert(target2, '5678') is None
        assert ring_mock_adt.insert(target3, '4321') is None
        new_node = ring_mock_adt.insert(target4, '8765')           # Node scaling up
        assert new_node is not None         
        assert new_node.index == 4999
        assert ring_mock_adt.get('1234') == target1
        assert ring_mock_adt.get('5678') == target2
        assert ring_mock_adt.get('4321') == target3
        assert ring_mock_adt.get('8765') == target4

    def test_scaling_down_node_zero_last(self, ring_mock_adt, mocker):
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
        assert ring_mock_adt.insert(target1, '0') is None
        assert ring_mock_adt.insert(target2, '1') is None
        assert ring_mock_adt.insert(target3, '3') is None
        new_node =  ring_mock_adt.insert(target4, '4')          # Node scaling up
        assert new_node is not None
        assert new_node.index == 2
        
        # The first target removal will scale down the cluster
        removed_node = ring_mock_adt.delete('4')
        assert removed_node is not None
        assert removed_node is not ring_mock_adt.node_zero
        # The second target is now in another node, so it will not scale down
        assert ring_mock_adt.delete('3') is None

        # The other targets are in the node_zero now, and ring should not scale down
        assert ring_mock_adt.delete('1') is None
        assert ring_mock_adt.delete('0') is None


    def test_scaling_down_node_zero_first(self, ring_mock_adt, mocker):
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

        assert ring_mock_adt.insert(target1, '500') is None
        assert ring_mock_adt.insert(target2, '5000') is None
        assert ring_mock_adt.insert(target3, '50000') is None         # Node scaling up
        assert ring_mock_adt.insert(target4, '500000') is not None
        print(ring_mock_adt.get_nodes())

        assert ring_mock_adt.delete('500') is None
        assert ring_mock_adt.node_zero.load == 50
        print(ring_mock_adt.get_nodes())
        assert ring_mock_adt.delete('5000') is None
        assert ring_mock_adt.node_zero.load == 25
        print(ring_mock_adt.get_nodes())

        # Removing all other targets. Node zero should not be deleted, so all returns None
        assert ring_mock_adt.delete('50000') is None
        deleted_node =  ring_mock_adt.delete('500000')
        assert deleted_node is not None
        assert deleted_node.index == 138875
        assert ring_mock_adt.node_zero.load == 0

    def test_insertion_many_targets_in_order(self, ring_mock_adt, mocker):
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
        assert ring_mock_adt.insert(target_list[0], target_list[0].id) is None
        assert ring_mock_adt.insert(target_list[1], target_list[1].id) is None
        assert ring_mock_adt.insert(target_list[2], target_list[2].id) is None
        assert ring_mock_adt.insert(target_list[3], target_list[3].id) is not None
        assert ring_mock_adt.insert(target_list[4], target_list[4].id) is None
        assert ring_mock_adt.insert(target_list[5], target_list[5].id) is not None
        assert ring_mock_adt.insert(target_list[6], target_list[6].id) is None
        assert ring_mock_adt.insert(target_list[7], target_list[7].id) is not None
        assert ring_mock_adt.insert(target_list[8], target_list[8].id) is None
        assert ring_mock_adt.insert(target_list[9], target_list[9].id) is not None

    def test_insertion_many_targets_in_order_discrepant_elements(self, ring_mock_adt, mocker):
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
        assert ring_mock_adt.insert(target_list[0], target_list[0].id) is None
        assert ring_mock_adt.insert(target_list[1], target_list[1].id) is None
        assert ring_mock_adt.insert(target_list[2], target_list[2].id) is None
        assert ring_mock_adt.insert(target_list[3], target_list[3].id) is not None
        assert ring_mock_adt.insert(target_list[4], target_list[4].id) is None
        assert ring_mock_adt.insert(target_list[5], target_list[5].id) is not None
        assert ring_mock_adt.insert(target_list[6], target_list[6].id) is None
        assert ring_mock_adt.insert(target_list[7], target_list[7].id) is not None
        assert ring_mock_adt.insert(target_list[8], target_list[8].id) is None
        assert ring_mock_adt.insert(target_list[9], target_list[9].id) is not None

    def test_deletion_many_targets_in_order(self, ring_mock_adt, mocker):
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
            ring_mock_adt.insert(target, target.id)
        assert ring_mock_adt.delete('90') is not None
        assert ring_mock_adt.delete('80') is None
        assert ring_mock_adt.delete('70') is not None
        assert ring_mock_adt.delete('60') is None
        assert ring_mock_adt.delete('50') is not None
        assert ring_mock_adt.delete('40') is None
        assert ring_mock_adt.delete('30') is not None
        assert ring_mock_adt.delete('20') is None
        assert ring_mock_adt.delete('10') is None
        assert ring_mock_adt.delete('0') is None

class TestBST:
    def test_insert_target(self, ring_bst):
        target = Target(id='1234', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
        ring_bst.insert(target, '1234')
        assert ring_bst.get('1234') == target

    def test_insert_duplicate_key(self, ring_bst):
        target = Target(id='1234', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
        ring_bst.insert(target, '1234')
        with pytest.raises(KeyAlreadyExistsError):
            ring_bst.insert(target, '1234')

    def test_get_nonexistent_key(self, ring_bst):
        with pytest.raises(KeyNotFoundError):
            ring_bst.get('nonexistent')

    def test_update_target(self, ring_bst):
        target = Target(id='1234', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
        ring_bst.insert(target, '1234')
        new_target = Target(id='1234', name='t2', address='t2-address', metrics_port=9000, metrics_path='/metrics')
        ring_bst.update('1234', new_target)
        assert ring_bst.get('1234') == new_target

    def test_delete_target(self, ring_bst):
        target = Target(id='1234', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
        ring_bst.insert(target, '1234')
        ring_bst.delete('1234')
        with pytest.raises(KeyNotFoundError):
            ring_bst.get('1234')

    def test_node_scaling_up(self, ring_bst, mocker):
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
        assert ring_bst.insert(target1, '1234') is None
        assert ring_bst.insert(target2, '5678') is None
        assert ring_bst.insert(target3, '4321') is None
        new_node = ring_bst.insert(target4, '8765')           # Node scaling up
        assert new_node is not None         
        assert new_node.index == 4999
        assert ring_bst.get('1234') == target1
        assert ring_bst.get('5678') == target2
        assert ring_bst.get('4321') == target3
        assert ring_bst.get('8765') == target4

    def test_scaling_down_node_zero_last(self, ring_bst, mocker):
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
        assert ring_bst.insert(target1, '0') is None
        assert ring_bst.insert(target2, '1') is None
        assert ring_bst.insert(target3, '3') is None
        new_node =  ring_bst.insert(target4, '4')          # Node scaling up
        assert new_node is not None
        assert new_node.index == 2
        
        # The first target removal will scale down the cluster
        removed_node = ring_bst.delete('4')
        assert removed_node is not None
        assert removed_node is not ring_bst.node_zero
        # The second target is now in another node, so it will not scale down
        assert ring_bst.delete('3') is None

        # The other targets are in the node_zero now, and ring should not scale down
        assert ring_bst.delete('1') is None
        assert ring_bst.delete('0') is None


    def test_scaling_down_node_zero_first(self, ring_bst, mocker):
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

        assert ring_bst.insert(target1, '500') is None
        assert ring_bst.insert(target2, '5000') is None
        assert ring_bst.insert(target3, '50000') is None         # Node scaling up
        assert ring_bst.insert(target4, '500000') is not None
        print(ring_bst.get_nodes())

        assert ring_bst.delete('500') is None
        assert ring_bst.node_zero.load == 50
        print(ring_bst.get_nodes())
        assert ring_bst.delete('5000') is None
        assert ring_bst.node_zero.load == 25
        print(ring_bst.get_nodes())

        # Removing all other targets. Node zero should not be deleted, so all returns None
        assert ring_bst.delete('50000') is None
        deleted_node =  ring_bst.delete('500000')
        assert deleted_node is not None
        assert deleted_node.index == 138875
        assert ring_bst.node_zero.load == 0

    def test_insertion_many_targets_in_order(self, ring_bst, mocker):
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
        assert ring_bst.insert(target_list[0], target_list[0].id) is None
        assert ring_bst.insert(target_list[1], target_list[1].id) is None
        assert ring_bst.insert(target_list[2], target_list[2].id) is None
        assert ring_bst.insert(target_list[3], target_list[3].id) is not None
        assert ring_bst.insert(target_list[4], target_list[4].id) is None
        assert ring_bst.insert(target_list[5], target_list[5].id) is not None
        assert ring_bst.insert(target_list[6], target_list[6].id) is None
        assert ring_bst.insert(target_list[7], target_list[7].id) is not None
        assert ring_bst.insert(target_list[8], target_list[8].id) is None
        assert ring_bst.insert(target_list[9], target_list[9].id) is not None

    def test_insertion_many_targets_in_order_discrepant_elements(self, ring_bst, mocker):
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
        assert ring_bst.insert(target_list[0], target_list[0].id) is None
        assert ring_bst.insert(target_list[1], target_list[1].id) is None
        assert ring_bst.insert(target_list[2], target_list[2].id) is None
        assert ring_bst.insert(target_list[3], target_list[3].id) is not None
        assert ring_bst.insert(target_list[4], target_list[4].id) is None
        assert ring_bst.insert(target_list[5], target_list[5].id) is not None
        assert ring_bst.insert(target_list[6], target_list[6].id) is None
        assert ring_bst.insert(target_list[7], target_list[7].id) is not None
        assert ring_bst.insert(target_list[8], target_list[8].id) is None
        assert ring_bst.insert(target_list[9], target_list[9].id) is not None

    def test_deletion_many_targets_in_order(self, ring_bst, mocker):
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
            ring_bst.insert(target, target.id)
        assert ring_bst.delete('90') is not None
        assert ring_bst.delete('80') is None
        assert ring_bst.delete('70') is not None
        assert ring_bst.delete('60') is None
        assert ring_bst.delete('50') is not None
        assert ring_bst.delete('40') is None
        assert ring_bst.delete('30') is not None
        assert ring_bst.delete('20') is None
        assert ring_bst.delete('10') is None
        assert ring_bst.delete('0') is None
