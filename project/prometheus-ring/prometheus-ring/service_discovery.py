from .target import Target
from .node import Node
import requests
import logging
import time

logger = logging.getLogger(__name__)
MAX_RETRIES = 5
class ServiceDiscovery:
    """
    For now, this implement only consul SD
    """
    def __init__(self, consul_url : str, consul_port : int = 8500):
        self.consul_url = consul_url
        self.consul_port = consul_port

    def register_target(self, target: Target, node: Node) -> None:
        payload = {
            "ID": target.id,
            "Name": target.name,
            "Tags": [f'ring-node-{str(node.index)}'],
            "Address": target.address,
            "Port": target.metrics_port
        }
        
        response = requests.put(f'http://{self.consul_url}:{self.consul_port}/v1/agent/service/register', json=payload)
        if response.status_code != 200:
            logger.error(f'Error registering target {target.id} in consul? {response.content}')
        else:
            logger.info(f'Target {target.id} registered in consul')

    def deregister_target(self, target: Target) -> None:
        response = requests.put(f'http://{self.consul_url}:{self.consul_port}/v1/agent/service/deregister/{target.id}')
        if response.status_code != 200:
            logger.error(f'Error deregistering target {target.id} in consul: {response.content}')
            if 'Unknown service ID' in response.text:               # There is a bug where sometimes the service is not found. Retrying to deregister
                for i in range(MAX_RETRIES):
                    logger.info(f'Retyring degister {target.id}. Atempo {i}')
                    response = requests.put(f'http://{self.consul_url}:{self.consul_port}/v1/agent/service/deregister/{target.id}')
                    if response.status_code == 200:
                        logger.info(f'Target {target.id} deregistered from consul')
                        break
                    time.sleep(0.5)
                logger.error(f'Error deregistering target {target.id} in consul: {response.content} after {MAX_RETRIES} retries')
        else:
            logger.info(f'Target {target.id} deregistered from consul')