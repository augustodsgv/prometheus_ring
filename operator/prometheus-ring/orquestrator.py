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
        self.containers: dict[list[str]]= dict()        # Keeps track of each instance and it's replicas

    def create_instance(
            self,
            node: Node,
            docker_networks: list[str] | str | None = None,
            environment: dict | None = None,
        )->None:
        """
        Instanciates a prometheus docker container and it's replicas
        """
        if environment is None:
            environment = dict()
        self.containers[node.index] = []

        environment['PROMETHEUS_YML'] = node.yaml
        for i in range(node.replica_count):
            container = self.client.containers.run(
                name=f'prometheus-{node.index}-{i}',
                image=self.prometheus_docker_image,
                network=self.api_network,
                environment=environment,
                detach=True,
            )
        
            self.containers[node.index].append(container)
            if docker_networks is not None:
                for network_name in docker_networks:
                    network = self.client.networks.get(network_name)
                    network.connect(container)

    def delete_instance(self, node: Node)->None:
        """
        Deletes a prometheus docker container
        """
        for container in self.containers.get(node.index):
            container.stop()
            container.remove()
            del self.containers[node.index]

    def check_instance_health(self)->None:
        ...
