from src.orquestrator.docker_orquestrator import DockerOrquestrator
from src.ring.prometheus_ring import PrometheusRing
from src.service_discovery.prometheus_ring_sd import PrometheusRingSD
from src.ring.target import Target

class API:
    def __init__(
            self,
            ring: PrometheusRing,
            service_discovery: PrometheusRingSD,
            orquestrator: DockerOrquestrator,
        )->None:

        self.ring = ring
        self.service_discovery = service_discovery
        self.orquestrator = orquestrator

    def register_target(self, target: Target)->None:
        """
        Registers a target to be monitored.
        Scales up the ring if the prometheus nodes are full.
        """
        new_node = self.ring.insert(target, target.id)         # Using the id as a hash, for now
        if new_node is not None:
            self.orquestrator.create_instance(new_node)
            # TODO: Implement some async call here
            # TODO: Also, should implement some kind of ensurance that the node is up and running
        
    def unregister_target(self, target: Target)->None:
        """
        Unregisters a target being monitored by prometheus.
        If the node is underloaded, scales down the ring
        """
        node_to_delete = self.ring.delete(target.id)         # Using the id as a hash, for now
        if node_to_delete is not None:
            self.orquestrator.delete_instance(node_to_delete)
        # TODO: Should implement an async call here

    def build_targets_json(self)->dict:
        targets_json: list[dict] = []
        nodes = self.prometheus_ring.get_nodes()
        for node in nodes:
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