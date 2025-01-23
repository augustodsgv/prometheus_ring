from .adt.abstract_data_type import AbstractDataType
from .node import Node
from .hash import stable_hash
from .target import Target

import uuid
import logging
logger = logging.getLogger(__name__)

class NodeNotFoundError(Exception):
    ...

class KeyNotFoundError(Exception):
    ...

class KeyAlreadyExistsError(Exception):
    ...

class Ring:
    def __init__(
            self,
            node_capacity: int,
            node_min_load: int,         # Using integer for simplicity. Varies from 0 to 100 (%)
            node_max_load: int,
            sd_url: str,
            sd_port: str,
            adt: AbstractDataType,
            node_replica_count: int = 1,
            node_sd_refresh_interval: str = '1m',
            node_scrape_interval: str = '1m',
            metrics_database_url: str | None = None,
            metrics_database_port: int | None = None,
            metrics_database_path: str | None = None,
        )->None:

        self.node_capacity = node_capacity
        self.node_min_load = node_min_load
        self.node_max_load = node_max_load
        self.node_replica_count = node_replica_count
        self.node_sd_refresh_interval = node_sd_refresh_interval
        self.node_scrape_interval = node_scrape_interval
        self.node_count = 1
        self.ring = adt
        self.sd_url = sd_url
        self.sd_port = sd_port
        self.metrics_database_url = metrics_database_url
        self.metrics_database_port = metrics_database_port
        self.metrics_database_path = metrics_database_path
        """
        Creating node zero. It can not be deleted.
        """
        self.node_zero = Node(
            index=0,
            capacity=node_capacity,
            sd_url=self.sd_url,
            sd_port=self.sd_port,
            replica_count=self.node_replica_count,
            refresh_interval=self.node_sd_refresh_interval,
            scrape_interval=self.node_scrape_interval,
            metrics_database_url=self.metrics_database_url,
            metrics_database_port=self.metrics_database_port,
            metrics_database_path=self.metrics_database_path,
            port=9090       # Port of the first node

            # TODO: Make an more versitile way to set the port
            )
        self.ring.insert(0, self.node_zero)

    def insert(self, target: Target, key: str | None = None)->None | Node:
        """
        Insert an target in the ring. If Ring scaled up, returns the node
        If a node reaches it's maximum load, a new node will be instanciated
        and the targets will be redistribuited
        """
        if key is None:
            key = str(uuid.uuid4())
        # Checking for duplicated keys. Current implementations does not support it
        node_to_search = self._find_node(stable_hash(key))
        if node_to_search.has_key(key):
            raise KeyAlreadyExistsError(f'Key {key} already exists')
        
        key_hash = stable_hash(key)
        print(f'key hash: {key_hash}')
        node_to_insert: Node = self._find_node(key_hash)
        logger.debug(f'Inserting {target} into node {node_to_insert}')
        node_to_insert.insert(key, target)

        if node_to_insert.load > self.node_max_load:                           # Detection if made after deletion to ensure it scales up at the right time
            logger.info(f'Node {node_to_insert.index} is full: scaling up the ring')
            new_node = self._split_node(node_to_insert)
            return new_node
        return None

    def get(self, key: str)->Node:
        """
        Returns the target of the key. Raises an exception if not found
        """
        key_hash = stable_hash(key)
        node_set_to_search: Node = self._find_node(key_hash)
        if not node_set_to_search.has_key(key):
            raise KeyNotFoundError(f'Key {key} not found')
        return node_set_to_search.get(key)

    def update(self, key: str, new_target: Target)->None:
        """
        Updates the Target of a key. Returns old object if update or None if didn't find
        Probly not useful in this implementation
        """
        key_hash = stable_hash(key)
        node_set_to_search: Node = self._find_node(key_hash)
        if not node_set_to_search.has_key(key):
            raise KeyNotFoundError(f'Key {key} not found')
        return node_set_to_search.update(key, new_target)
        
    def delete(self, key: str)->None | Node:
        """
        Deletes a target from the ring.
        If node reachs it's minimum load, it will be removed from the ring
        """
        key_hash = stable_hash(key)
        node_to_search: Node = self._find_node(key_hash)
        if not node_to_search.has_key(key):
            raise KeyNotFoundError(f'Key {key} not found')
        # TODO: If the previous node is full, it will be overloaded. Should implement something to treat this
        node_to_search.delete(key)
        if node_to_search.load <= self.node_min_load:            # Scaling down the cluster
            if node_to_search == self.node_zero:
                """
                We can't delete node zero.
                In current implementation, the node zero can be underloaded to make it simples
                """
                print('node zero: not deleting')
                return None
            logger.info(f'Node {node_to_search.index} is underloaded: scaling down the ring')
            self._delete_node(node_to_search.index)
            return node_to_search
        return None

    def get_nodes(self)->list[Node]:
        """
        Returns a list of all nodes in the ring
        """
        return self.ring.list()

    def _find_node(self, hash: int)->Node:
        """
        Finds the nearest node to a hash, i.e. the greatest node that is smaler than the provided hash
        """
        return self.ring.find_max_smaller_than(hash)
        
    def _split_node(self, node: Node)->Node:
        """
        Splits the node in two, creating a new node with the new_node_index
        Returns the new node
        """
        node_mid_hash = node.calc_mid_hash()        # The new node will get half of the keys of the old node.
        print(node_mid_hash)
        new_node = Node(
            index=node_mid_hash,
            capacity=self.node_capacity,
            replica_count=self.node_replica_count,
            sd_url=self.sd_url,
            sd_port=self.sd_port,
            scrape_interval=self.node_scrape_interval,
            refresh_interval=self.node_sd_refresh_interval,
            metrics_database_url=self.metrics_database_url,
            metrics_database_port=self.metrics_database_port,
            metrics_database_path=self.metrics_database_path,
        )
        self.ring.insert(node_mid_hash, new_node)
        node.export_keys(new_node, node_mid_hash)
        self.node_count += 1

        logger.info(f'New node created with index {node_mid_hash}')
        return new_node

    def _delete_node(self, index: int)->Node:
        """
        Deletes a node and sends it's targets to the previous node.
        Returns de deleted node.
        """
        # TODO: check if the prior node has capacity to receive the keys
        node_to_delete: Node = self.ring.search(index)
        if node_to_delete is None:
            logger.info(f'Node with index {index} not found to delete')
            raise NodeNotFoundError(f'Node with index {index} not found')
        prior_node: Node = self.ring.find_max_smaller_than(index - 1)       # Ensures
        print(f'prior node: {prior_node}')
        logger.info(f'Exporting Keys of node {index} to the node {prior_node.index}')
        node_to_delete.export_keys(prior_node, 0)           # Uses 0 to ensure that all of if keys are exported
        self.ring.remove(index)
        logger.info(f'Node {index} removed from the ring successfully')
        return node_to_delete

    # # Prometheus specific methods
    # def set_node_not_ready(self, node_index: int)->None:
    #     """
    #     Sets a node as not ready to receive requests
    #     """
    #     node: Node = self.ring.search(node_index)
    #     if node is None:
    #         raise NodeNotFoundError(f'Node with index {node_index} not found')
    #     node.ready = False