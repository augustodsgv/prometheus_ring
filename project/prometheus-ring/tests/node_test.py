import pytest
import pytest_mock
from prometheus_ring.node import Node
from prometheus_ring.target import Target
from prometheus_ring.hash import stable_hash
import math

def test_insert_one_target():
    t1 = Target(id='1234', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    node = Node(index=0, capacity=10)
    node.insert('1234', t1)
    assert node.get('1234') == t1

def test_prometheus_node_zero_yaml():
    node = Node(index=0, capacity=10, replica_count=1, sd_url='localhost', sd_port='9090')
    expected_yaml = """global:
  scrape_interval: 1m
  external_labels:
    cluster: node-0
    __replica__: a
scrape_configs:
- job_name: prometheus_ring_sd
  http_sd_configs:
  - url: http://localhost:9090/targets
    refresh_interval: 1m
  relabel_configs:
  - action: keep
    source_labels:
    - node_index
    regex: '0'
"""
    print(expected_yaml)
    print(node.get_node_yamls()['node-0-a'])
    assert node.get_node_yamls()['node-0-a'] == expected_yaml


def test_prometheus_other_node_yaml():
    node = Node(
        index=234,
        capacity=15,
        replica_count=1,
        sd_url='prometheus-ring',
        sd_port='9988',
        scrape_interval='15s',
        refresh_interval='45m',
        port='8899', 
    )
    expected_yaml = """global:
  scrape_interval: 15s
  external_labels:
    cluster: node-234
    __replica__: a
scrape_configs:
- job_name: prometheus_ring_sd
  http_sd_configs:
  - url: http://prometheus-ring:9988/targets
    refresh_interval: 45m
  relabel_configs:
  - action: keep
    source_labels:
    - node_index
    regex: '234'
"""
    assert node.get_node_yamls()['node-234-a'] == expected_yaml

def test_prometheus_multiple_replicas():
    node = Node(
        index=5678,
        capacity=15,
        replica_count=1,
        sd_url='prometheus-ring',
        sd_port='9988',
        scrape_interval='15s',
        refresh_interval='45m',
        port='8899', 
    )
    expected_yaml_a = """global:
  scrape_interval: 15s
  external_labels:
    cluster: node-5678
    __replica__: a
scrape_configs:
- job_name: prometheus_ring_sd
  http_sd_configs:
  - url: http://prometheus-ring:9988/targets
    refresh_interval: 45m
  relabel_configs:
  - action: keep
    source_labels:
    - node_index
    regex: '5678'
"""
    expected_yaml_b = """global:
  scrape_interval: 15s
  external_labels:
    cluster: node-5678
    __replica__: b
scrape_configs:
- job_name: prometheus_ring_sd
  http_sd_configs:
  - url: http://prometheus-ring:9988/targets
    refresh_interval: 45m
  relabel_configs:
  - action: keep
    source_labels:
    - node_index
    regex: '5678'
"""

    expected_yaml_c = """global:
  scrape_interval: 15s
  external_labels:
    cluster: node-5678
    __replica__: c
scrape_configs:
- job_name: prometheus_ring_sd
  http_sd_configs:
  - url: http://prometheus-ring:9988/targets
    refresh_interval: 45m
  relabel_configs:
  - action: keep
    source_labels:
    - node_index
    regex: '5678'
"""
    assert node.get_node_yamls()['node-5678-a'] == expected_yaml_a
    assert node.get_node_yamls()['node-5678-b'] == expected_yaml_b
    assert node.get_node_yamls()['node-5678-c'] == expected_yaml_c


def test_prometheus_remote_storage_yaml():
    node = Node(
        index=7,
        capacity=15,
        replica_count=6,
        sd_url='prometheus-ring',
        sd_port='9988',
        scrape_interval='15s',
        refresh_interval='45m',
        port='8899',
        metrics_database_url='database',
        metrics_database_port=19090,
        metrics_database_path='/api/v1/push'
    )
    expected_yaml = """global:
  scrape_interval: 15s
  external_labels:
    cluster: node-7
    __replica__: f
scrape_configs:
- job_name: prometheus_ring_sd
  http_sd_configs:
  - url: http://prometheus-ring:9988/targets
    refresh_interval: 45m
  relabel_configs:
  - action: keep
    source_labels:
    - node_index
    regex: '7'
remote_write:
- url: http://database:19090/api/v1/push
  headers:
    X-Scope-OrgID: demo
"""
    assert node.get_node_yamls()['node-7-f'] == expected_yaml

def test_node_is_full():
    node = Node(index=0, capacity=1)
    t1 = Target(id='1234', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    node.insert('1234', t1)
    assert node.is_full() == True

def test_node_is_not_full():
    node = Node(index=0, capacity=2)
    t1 = Target(id='1234', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    node.insert('1234', t1)
    assert node.is_full() == False

def test_delete_target():
    node = Node(index=0, capacity=10)
    t1 = Target(id='1234', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    node.insert('1234', t1)
    node.delete('1234')
    assert node.get('1234') is None

def test_update_target():
    node = Node(index=0, capacity=10)
    t1 = Target(id='1234', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    t2 = Target(id='1234', name='new-t1', address='t1-address', metrics_port=9000, metrics_path='/metrics')
    node.insert('1234', t1)
    node.update('1234', t2)
    assert node.get('1234') == t2

def test_node_load_0():
    node = Node(index=0, capacity=2)
    assert node.load == 0

def test_node_load_50():
    node = Node(index=0, capacity=2)
    t1 = Target(id='1234', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    node.insert('1234', t1)
    assert node.load == 50

def test_node_load_100():
    node = Node(index=0, capacity=2)
    t1 = Target(id='1234', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    t2 = Target(id='5678', name='t2', address='t2-address', metrics_port=8000, metrics_path='/metrics')
    node.insert('1234', t1)
    node.insert('5678', t2)
    assert node.load == 100

def test_node_load_33():
    node = Node(index=0, capacity=3)
    t1 = Target(id='1234', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    node.insert('1234', t1)
    assert node.load == 33

def test_node_load_50_after_deletion():
    node = Node(index=0, capacity=2)
    t1 = Target(id='1234', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    t2 = Target(id='5678', name='t2', address='t2-address', metrics_port=8000, metrics_path='/metrics')
    node.insert('1234', t1)
    node.insert('5678', t2)
    node.delete('1234')
    assert node.load == 50

def test_calc_mid_hash_even_elements(mocker):
    # Mocking the hash function to test the calc_mid_hash
    mocker.patch('prometheus_ring.node.stable_hash', side_effect=lambda x: int(x))

    node1 = Node(index=0, capacity=10)
    t1 = Target(id='1', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    t2 = Target(id='2', name='t2', address='t2-address', metrics_port=8000, metrics_path='/metrics')
    t3 = Target(id='3', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    t4 = Target(id='7', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    node1.insert('1', t1)
    node1.insert('2', t2)
    node1.insert('3', t3)
    node1.insert('7', t4)

    assert node1.calc_mid_hash() == 3

def test_calc_mid_hash_odd_elements(mocker):
    # Mocking the hash function to test the calc_mid_hash
    mocker.patch('prometheus_ring.node.stable_hash', side_effect=lambda x: int(x))

    node1 = Node(index=0, capacity=10)
    t1 = Target(id='1', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    t2 = Target(id='2', name='t2', address='t2-address', metrics_port=8000, metrics_path='/metrics')
    t3 = Target(id='3', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    t4 = Target(id='15', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    t5 = Target(id='51', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    node1.insert('1', t1)
    node1.insert('2', t2)
    node1.insert('3', t3)
    node1.insert('15', t4)
    node1.insert('51', t5)

    assert node1.calc_mid_hash() == 14

def test_calc_mid_hash_discrepant_even_elements(mocker):
    # Mocking the hash function to test the calc_mid_hash
    mocker.patch('prometheus_ring.node.stable_hash', side_effect=lambda x: int(x))

    node1 = Node(index=0, capacity=10)
    t1 = Target(id='1', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    t2 = Target(id='2', name='t2', address='t2-address', metrics_port=8000, metrics_path='/metrics')
    t3 = Target(id='7', name='t3', address='t3-address', metrics_port=8000, metrics_path='/metrics')
    t4 = Target(id='500', name='t4', address='t4-address', metrics_port=8000, metrics_path='/metrics')
    t5 = Target(id='5001', name='t5', address='t5-address', metrics_port=8000, metrics_path='/metrics')
    t6 = Target(id='18000', name='t6', address='t6-address', metrics_port=8000, metrics_path='/metrics')
    node1.insert('1', t1)
    node1.insert('2', t2)
    node1.insert('7', t3)
    node1.insert('500', t4)
    node1.insert('5001', t5)
    node1.insert('18000', t6)
    mean = 3918
    assert node1.calc_mid_hash() == mean

def test_calc_mid_hash_discrepant_odd_elements(mocker):
    # Mocking the hash function to test the calc_mid_hash
    mocker.patch('prometheus_ring.node.stable_hash', side_effect=lambda x: int(x))

    node1 = Node(index=0, capacity=10)
    t1 = Target(id='1', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    t2 = Target(id='1234', name='t2', address='t2-address', metrics_port=8000, metrics_path='/metrics')
    t3 = Target(id='4321', name='t3', address='t3-address', metrics_port=8000, metrics_path='/metrics')
    t4 = Target(id='500', name='t4', address='t4-address', metrics_port=8000, metrics_path='/metrics')
    t5 = Target(id='5001', name='t5', address='t5-address', metrics_port=8000, metrics_path='/metrics')
    node1.insert('1', t1)
    node1.insert('1234', t2)
    node1.insert('4321', t3)
    node1.insert('500', t4)
    node1.insert('5001', t5)

    assert node1.calc_mid_hash() == 2211

def test_export_keys():
    node1 = Node(index=0, capacity=10)
    node2 = Node(index=1, capacity=10)
    t1 = Target(id='1234', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    node1.insert('t1', t1)
    node1.export_keys(node2)
    assert node2.get('t1') == t1
    assert node1.get('t1') is None

def test_export_half_keys():
    node1 = Node(index=0, capacity=10)
    node2 = Node(index=1, capacity=10)
    t1 = Target(id='1234', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    t2 = Target(id='5678', name='t2', address='t2-address', metrics_port=8000, metrics_path='/metrics')
    t3 = Target(id='4321', name='t3', address='t3-address', metrics_port=8000, metrics_path='/metrics')
    t4 = Target(id='8765', name='t4', address='t5-address', metrics_port=8000, metrics_path='/metrics')
    node1.insert('1234', t1)
    node1.insert('5678', t2)
    node1.insert('4321', t3)
    node1.insert('8765', t4)

    # Once hash is an one-way function, neet to keep track of it
    hash_to_ids = {
        stable_hash('1234'): '1234',
        stable_hash('5678'): '5678',
        stable_hash('4321'): '4321',
        stable_hash('8765'): '8765'
    }

    hashed_ids = sorted(hash_to_ids.keys())             # I don't know the hashes, so i calculate them and sorted 
    node1.export_keys(node2, hashed_ids[2])             # Taking the third element, so it's divided equally

    # Ensuring the first 2 are in node one and the last two are not
    assert node1.get(hash_to_ids[hashed_ids[0]]) is not None
    assert node1.get(hash_to_ids[hashed_ids[1]]) is not None
    assert node1.get(hash_to_ids[hashed_ids[2]]) is None
    assert node1.get(hash_to_ids[hashed_ids[3]]) is None

    # Ensuring the last 2 are in node two and the last two are
    assert node2.get(hash_to_ids[hashed_ids[0]]) is None
    assert node2.get(hash_to_ids[hashed_ids[1]]) is None
    assert node2.get(hash_to_ids[hashed_ids[2]]) is not None
    assert node2.get(hash_to_ids[hashed_ids[3]]) is not None

def test_export_even_number_of_keys():
    node1 = Node(index=0, capacity=10)
    node2 = Node(index=1, capacity=10)
    t1 = Target(id='1234', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    t2 = Target(id='5678', name='t2', address='t2-address', metrics_port=8000, metrics_path='/metrics')
    t3 = Target(id='4321', name='t3', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    t4 = Target(id='8765', name='t4', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    t5 = Target(id='abcd', name='t5', address='t1-address', metrics_port=8000, metrics_path='/metrics')

    node1.insert('1234', t1)
    node1.insert('5678', t2)
    node1.insert('4321', t3)
    node1.insert('8765', t4)
    node1.insert('abcd', t5)

    # Once hash is an one-way function, need to keep track of it
    hash_to_ids = {
        stable_hash('1234'): '1234',
        stable_hash('5678'): '5678',
        stable_hash('4321'): '4321',
        stable_hash('8765'): '8765',
        stable_hash('abcd'): 'abcd'
    }

    hashed_ids = sorted(hash_to_ids.keys())             # I don't know the hashes, so i calculate them and sorted 
    node1.export_keys(node2, hashed_ids[2])             # Taking the third element, so it's divided equally

    # Ensuring the first 2 are in node one and the last two are not
    assert node1.get(hash_to_ids[hashed_ids[0]]) is not None
    assert node1.get(hash_to_ids[hashed_ids[1]]) is not None
    assert node1.get(hash_to_ids[hashed_ids[2]]) is None
    assert node1.get(hash_to_ids[hashed_ids[3]]) is None
    assert node1.get(hash_to_ids[hashed_ids[4]]) is None

    # Ensuring the last 2 are in node two and the last two are
    assert node2.get(hash_to_ids[hashed_ids[0]]) is None
    assert node2.get(hash_to_ids[hashed_ids[1]]) is None
    assert node2.get(hash_to_ids[hashed_ids[2]]) is not None
    assert node2.get(hash_to_ids[hashed_ids[3]]) is not None
    assert node2.get(hash_to_ids[hashed_ids[4]]) is not None

