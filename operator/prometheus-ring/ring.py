from .adt.abstract_data_type import AbstractDataType
from .node import Node
from .hash import stable_hash
from .target import Target
import threading
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
            sd_provider: str, 
            sd_host: str,
            sd_port: str,
            adt: AbstractDataType,
            node_replica_count: int = 1,
            node_base_ports: int = 19090,       # First port that a node will pick. Next nodes will have incremental ports
            sd_refresh_interval: str = '1m',
            node_scrape_interval: str = '1m',
            node_scrape_timeout: str = '20s',
            metrics_database_url: str | None = None,
            metrics_database_port: int | None = None,
            metrics_database_path: str | None = None,
        )->None:
        self.node_capacity = node_capacity
        self.node_min_load = node_min_load
        self.node_max_load = node_max_load
        self.node_replica_count = node_replica_count
        self.node_base_ports = node_base_ports
        self.node_scrape_interval = node_scrape_interval
        self.node_scrape_timeout = node_scrape_timeout
        self.node_count = 0
        self.sd_provider = sd_provider
        self.sd_host = sd_host
        self.sd_port = sd_port
        self.sd_refresh_interval = sd_refresh_interval
        self.metrics_database_url = metrics_database_url
        self.metrics_database_port = metrics_database_port
        self.metrics_database_path = metrics_database_path
        
        self.ring = adt
        self.ring_lock = threading.Lock()

        """
        Creating node zero. It can not be deleted.
        """
        self.node_zero = Node(
            index=0,
            capacity=node_capacity,
            sd_provider=self.sd_provider,
            sd_host=self.sd_host,
            sd_port=self.sd_port,
            replica_count=self.node_replica_count,
            sd_refresh_interval=self.sd_refresh_interval,
            scrape_interval=self.node_scrape_interval,
            scrape_timeout=self.node_scrape_timeout,
            metrics_database_url=self.metrics_database_url,
            metrics_database_port=self.metrics_database_port,
            metrics_database_path=self.metrics_database_path,
            port=self.node_base_ports + self.node_count
            # TODO: Make an more versitile way to set the port
            )
        self.node_count += 1
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
        with self.ring_lock:
            node_to_insert: Node = self._find_node(key_hash)
            logger.debug(f'Inserting {target} into node {node_to_insert}')
            
            node_to_insert.insert(key, target)

            if node_to_insert.load > self.node_max_load:                           # Detection if made after deletion to ensure it scales up at the right time
                logger.info(f'Node {node_to_insert.index} is full: scaling up the ring')
                new_node = self._split_node(node_to_insert)
                return new_node
            return None

    def get(self, key: str)->Target:
        """
        Returns the target of the key. Raises an exception if not found
        """
        key_hash = stable_hash(key)
        node_set_to_search: Node = self._find_node(key_hash)
        if not node_set_to_search.has_key(key):
            raise KeyNotFoundError(f'Key {key} not found')
        return node_set_to_search.get(key)

    def get_target_node(self, key: str)->Node:
        """
        Returns the node a target belongs to
        """
        key_hash = stable_hash(key)
        node_set_to_search: Node = self._find_node(key_hash)
        if not node_set_to_search.has_key(key):
            raise KeyNotFoundError(f'Key {key} not found')
        return node_set_to_search

    def update(self, key: str, new_target: Target)->None:
        """
        Updates the Target of a key. Returns old object if update or None if didn't find
        Probly not useful in this implementation
        """
        with self.ring_lock:
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
        with self.ring_lock:
            node_to_search: Node = self._find_node(key_hash)
            logger.debug(f'Deleting key {key} {key_hash} from node {node_to_search.index}')
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
                    logger.debug('node zero: not deleting')
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
        return self.ring.find_max_smaller_than(hash + 1)            # +1 so if a node hash the same value it will be included
        
    def _split_node(self, node: Node)->Node:
        """
        Splits the node in two, creating a new node with the new_node_index
        Returns the new node
        """
        node_mid_hash = node.calc_mid_hash()        # The new node will get half of the keys of the old node.
        logger.debug(node_mid_hash)
        new_node = Node(
            index=node_mid_hash,
            capacity=self.node_capacity,
            replica_count=self.node_replica_count,
            sd_provider=self.sd_provider,
            sd_host=self.sd_host,
            sd_port=self.sd_port,
            scrape_interval=self.node_scrape_interval,
            scrape_timeout=self.node_scrape_timeout,
            sd_refresh_interval=self.sd_refresh_interval,
            metrics_database_url=self.metrics_database_url,
            metrics_database_port=self.metrics_database_port,
            metrics_database_path=self.metrics_database_path,
            port=self.node_base_ports + self.node_count
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
        # TODO: check if the prior node has capacity to receive the keys or launch new node after insertion
        node_to_delete: Node = self.ring.search(index)
        if node_to_delete is None:
            logger.info(f'Node with index {index} not found to delete')
            raise NodeNotFoundError(f'Node with index {index} not found')
        prior_node: Node = self.ring.find_max_smaller_than(index)       # Ensures
        logger.debug(f'prior node: {prior_node}')
        logger.debug(f'Exporting Keys of node {index} to the node {prior_node.index}')
        node_to_delete.export_keys(prior_node, 0)           # Uses 0 to ensure that all of if keys are exported
        self.ring.remove(index)
        logger.debug(f'Node {index} removed from the ring successfully')
        return node_to_delete
