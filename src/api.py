from src.orquestrator.docker_orquestrator import DockerOrquestrator
from src.ring.prometheus_ring import PrometheusRing
from src.service_discovery.prometheus_ring_sd import PrometheusRingSD
from src.ring.target import Target
import logging

logger = logging.getLogger(__name__)

class API:
    def __init__(
            self,
            ring: PrometheusRing,
            orquestrator: DockerOrquestrator,
        )->None:

        self.ring = ring
        self.orquestrator = orquestrator

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
            # TODO: Also, should implement some kind of ensurance that the node is up and running
        
    def unregister_target(self, target_id)->None:
        """
        Unregisters a target being monitored by prometheus.
        If the node is underloaded, scales down the ring
        """
        node_to_delete = self.ring.delete(target_id)         # Using the id as a hash, for now
        if node_to_delete is not None:
            self.orquestrator.delete_instance(node_to_delete)
        # TODO: Should implement an async call here

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