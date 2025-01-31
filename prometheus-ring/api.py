from .orquestrator import Orquestrator
from .ring import Ring
from .target import Target
from .service_discovery import ServiceDiscovery
import logging

logger = logging.getLogger(__name__)

class API:
    def __init__(
            self,
            ring: Ring,
            orquestrator: Orquestrator,
            service_discovery: ServiceDiscovery | None
        )->None:

        self.ring = ring
        self.orquestrator = orquestrator
        self.service_discovery = service_discovery

    def register_target(self, target: Target)->None:
        """
        Registers a target to be monitored.
        Scales up the ring if the prometheus nodes are full.
        """
        new_node = self.ring.insert(target, target.id)         # Using the id as a hash, for now
        logger.debug(f'iserting target {target}')
        if new_node is not None:
            self.orquestrator.create_instance(new_node)
            # TODO: Implement some async call here

        # Registering targets in the service discovery
        if self.service_discovery is not None:
            inserted_node = self.ring.get_target_node(target.id)
            self.service_discovery.register_target(target, inserted_node)

            if new_node is not None:
                # Registering the targets in the service discovery to new node
                for target in new_node.list_items():
                    self.service_discovery.deregister_target(target)        # Deregistering the target from the old node
                    self.service_discovery.register_target(target, new_node)
            
        
    def unregister_target(self, target_id)->None:
        """
        Unregisters a target being monitored by prometheus.
        If the node is underloaded, scales down the ring
        """
        logger.debug(f'nodes: {self.ring.get_nodes()}')
        target = self.ring.get(target_id)
        self.service_discovery.register_target(target)

        node_to_delete = self.ring.delete(target_id)         # Using the id as a hash, for now
        if node_to_delete is not None:
            self.orquestrator.delete_instance(node_to_delete)

        # Deregistering the target from the service discovery
        if self.service_discovery is not None:
            self.service_discovery.deregister_target(target)
            if node_to_delete is not None:
                # Registering the targets in the service discovery to new node
                moved_targets = node_to_delete.list_items()
                new_node = self.ring.get_target_node(moved_targets[0].id)     # All targets from the same node
                for target in moved_targets:
                    self.service_discovery.deregister_target(target)
                    self.service_discovery.register_target(target, new_node)

    def build_targets_json(self)->dict:
        targets_json: list[dict] = []
        nodes = self.ring.get_nodes()
        logger.debug(f'Nodes: {nodes}')
        for node in nodes:
            print(node)
            logger.debug(f'node: {node}')
            targets = node.list_items()
            targets_json.append(
                {
                    'targets': [target.endpoint for target in targets],
                    'labels': {
                        'node_index': str(node.index),
                        '__metrics__path__': '/metrics'
                    }
                }
            )
        return targets_json