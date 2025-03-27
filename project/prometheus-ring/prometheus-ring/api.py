from .orquestrator import Orquestrator
from .swarm_orquestrator import SwarmOrquestrator
from .ring import Ring, KeyNotFoundError
from .target import Target
from .service_discovery import ServiceDiscovery
import logging

logger = logging.getLogger(__name__)

class API:
    def __init__(
            self,
            ring: Ring,
            orquestrator: SwarmOrquestrator,
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
        logger.debug(f'inserting target {target}')
        if new_node is not None:
            self.orquestrator.create_node(new_node)
            # TODO: Implement some async call here

    # def register_target(self, target: Target)->None:
    #     """
    #     Registers a target to be monitored.
    #     Scales up the ring if the prometheus nodes are full.
    #     """
    #     new_node = self.ring.insert(target, target.id)         # Using the id as a hash, for now
    #     logger.debug(f'inserting target {target}')
    #     if new_node is not None:
    #         self.orquestrator.create_node(new_node)
    #         # TODO: Implement some async call here

    #     # Registering targets in the service discovery

    #     inserted_node = self.ring.get_target_node(target.id)
    #     if inserted_node is not None:
    #         if self.service_discovery is not None:
    #             self.service_discovery.register_target(target, inserted_node)

    #         if new_node is not None:
    #             # Registering the targets in the service discovery to new node
    #             for target in new_node.list_items():
    #                 self.service_discovery.deregister_target(target)        # Deregistering the target from the old node
    #                 self.service_discovery.register_target(target, new_node)                
       

    def unregister_target(self, target_id)->None:
        """
        Unregisters a target being monitored by prometheus.
        If the node is underloaded, scales down the ring
        """
        logger.debug(f'nodes: {self.ring.get_nodes()}')
        
        try:
            self.ring.get(target_id)
            node_to_delete = self.ring.delete(target_id)                        # Returns a node if ring scaled down
            if node_to_delete is not None:
                self.orquestrator.delete_node(node_to_delete)                      # Removing previous node

        except KeyNotFoundError:
            # TODO: treat this
            pass

    # def unregister_target(self, target_id)->None:
    #     """
    #     Unregisters a target being monitored by prometheus.
    #     If the node is underloaded, scales down the ring
    #     """
    #     logger.debug(f'nodes: {self.ring.get_nodes()}')
        
    #     try:
    #         target = self.ring.get(target_id)
    #         node_to_delete = self.ring.delete(target_id)                        # Returns a node if ring scaled down
    #         if self.service_discovery is not None:
    #             self.service_discovery.deregister_target(target)

    #         if node_to_delete is not None:
    #             self.orquestrator.delete_node(node_to_delete)                      # Removing previous node
    #             if self.service_discovery is not None:
    #                 targets_to_relocate = node_to_delete.list_items()
    #                 logger.debug(f'targets to relocate: {targets_to_relocate}')
    #                 if len(targets_to_relocate) > 0:        # Checking if there are targets to relocate
    #                     previous_node = self.ring.get_target_node(targets_to_relocate[0].id)     # All targets from the same node
    #                     for target in targets_to_relocate:
    #                         self.service_discovery.deregister_target(target)
    #                         self.service_discovery.register_target(target, previous_node)
    #                 # TODO: should implement something here to ensure that the previous node already started collection metrics
                    



    def build_targets_json(self)->dict:
        targets_json: list[dict] = []
        nodes = self.ring.get_nodes()
        logger.debug(f'Nodes: {nodes}')
        for node in nodes:
            logger.debug(f'node: {node}')
            targets = node.list_items()
            # TODO: this is very bad for performance, but is simpler to implement;
            # maybe we can make this a background task or something
            for target in targets:
                targets_json.append(
                    {
                        'targets': [target.endpoint],
                        'labels': {
                            'node_index': str(node.index),
                            '__metrics__path__': '/metrics',
                            'target_id': target.id,
                        }
                    }
                )
        return targets_json