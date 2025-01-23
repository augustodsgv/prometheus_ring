from .node import Node
import docker
import base64

class Orquestrator:
    """
    Docker wrapper to create and delete prometheus nodes
    """
    def __init__(
            self,
            prometheus_docker_image: str = 'prom/prometheus',
            api_network: str = 'prometheus-ring-api-network',
            docker_url: str = 'unix://var/run/docker.sock'
        )->None:
        self.client = docker.DockerClient(base_url=docker_url)
        try:
            self.client.networks.get(api_network)
        except docker.errors.NotFound:
            self.client.networks.create(api_network)

        self.api_network = api_network
        self.prometheus_docker_image = prometheus_docker_image
        self.docker_url = docker_url
        self.containers = dict()
        
    def create_instance(
            self,
            node: Node,
            docker_networks: list[str] | str | None = None,
            environment: dict | None = None,
        )->None:
        """
        Instanciates a prometheus docker container
        """
        if environment is None:
            environment = dict()
        environment['PROMETHEUS_YML'] = base64.b64encode(node.yaml.encode('utf-8'))
        container = self.client.containers.run(
            name='prometheus-ring-' + str(node.index),
            image=self.prometheus_docker_image,
            network=self.api_network,
            environment=environment,
            detach=True,
            ports={node.port: node.port} if node.port is not None else None
        )
    
        self.containers[node.index] = container
        if docker_networks is not None:
            for network_name in docker_networks:
                network = self.client.networks.get(network_name)
                network.connect(container)

    def delete_instance(self, node: Node)->None:
        """
        Deletes a prometheus docker container
        """
        container = self.containers.get(node.index)
        if container is not None:
            container.stop()
            container.remove()
            del self.containers[node.index]

    def check_instance_health(self)->None:
        ...
