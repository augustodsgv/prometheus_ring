from src.ring.prometheus_ring import PrometheusRing
from src.service_discovery.service_discovery import ServiceDiscovery
from src.ring.target import Target
from src.ring.node import Node

class PrometheusRingSD(ServiceDiscovery):
    def __init__(
            self,
            prometheus_ring: PrometheusRing,
        )->None:
        self.prometheus_ring = prometheus_ring

    def register_target(self, target: Target) -> None:
        self.prometheus_ring.insert(target, target.id)

    def deregister_target(self, target: Target) -> None:
        self.prometheus_ring.delete(target.id)

    def get_targets_json(self) -> list[dict]:
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

