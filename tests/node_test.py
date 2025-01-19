import pytest
from prometheus_ring.node import Node
from prometheus_ring.target import Target
from prometheus_ring.hash import hash

def test_insert_one_target():
    t1 = Target(id='1234', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    node = Node(index=0, capacity=10)
    node.insert('1234', t1)
    assert node.get('1234') == t1

def test_prometheus_node_zero_yaml():
    node = Node(index=0, capacity=10, sd_url='localhost', sd_port='9090')
    expected_yaml = """global:
  scrape_interval: 1m
scrape_configs:
- job_name: prometheus_ring_sd
  http_sd_configs:
  - url: http://localhost:9090/targets
    refresh_interval: 1m
  relabel_configs:
  - action: keep
    source_labels:
    - index
    regex: '0'
"""
    assert node.yaml == expected_yaml

def test_prometheus_other_node_yaml():
    node = Node(
        index=1234,
        capacity=15,
        sd_url='prometheus-ring',
        sd_port='9988',
        scrape_interval='15s',
        refresh_interval='45m',
        port='8899', 
    )
    expected_yaml = """global:
  scrape_interval: 15s
scrape_configs:
- job_name: prometheus_ring_sd
  http_sd_configs:
  - url: http://prometheus-ring:9988/targets
    refresh_interval: 45m
  relabel_configs:
  - action: keep
    source_labels:
    - index
    regex: '1234'
"""
    assert node.yaml == expected_yaml

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

def test_calc_mid_hash():
    node1 = Node(index=0, capacity=10)
    t1 = Target(id='1234', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    t2 = Target(id='5678', name='t2', address='t2-address', metrics_port=8000, metrics_path='/metrics')
    t3 = Target(id='4321', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    t4 = Target(id='8765', name='t1', address='t1-address', metrics_port=8000, metrics_path='/metrics')
    node1.insert('1234', t1)
    node1.insert('5678', t2)
    node1.insert('4321', t3)
    node1.insert('8765', t4)

    ids = ['1234', '5678', '4321', '8765']
    hashed_ids = [hash(id) for id in ids]              # I don't know the hashes, so i calculate them
    hash_mean = sum(hashed_ids) // 4
    print(hash_mean)
    print(hashed_ids)
    assert node1.calc_mid_hash() == hash_mean

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
        hash('1234'): '1234',
        hash('5678'): '5678',
        hash('4321'): '4321',
        hash('8765'): '8765'
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
        hash('1234'): '1234',
        hash('5678'): '5678',
        hash('4321'): '4321',
        hash('8765'): '8765',
        hash('abcd'): 'abcd'
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

