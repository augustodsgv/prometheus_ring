from .orquestrator import Orquestrator
from src.ring.prometheus_node import PrometheusNode
import docker
import base64

class DockerOrquestrator(Orquestrator):
    def __init__(
            self,
            prometheus_docker_image: str = 'prom/prometheus',
            docker_url: str = 'unix://var/run/docker.sock'
        )->None:

        self.prometheus_docker_image = prometheus_docker_image
        self.docker_url = docker_url
        self.client = docker.DockerClient(base_url=self.docker_url)
        self.containers = dict()
        
    def create_instance(
            self,
            prometheusNode: PrometheusNode,
            docker_network: str | None = None,
            environment: dict | None = None
        )->None:
        """
        Instanciates a prometheus docker container
        """
        if environment is None:
            environment = dict()
        environment['PROMETHEUS_YML'] = base64.b64encode(prometheusNode.yaml.encode('utf-8'))
        container = self.client.containers.run(
            name='prometheus-ring-' + str(prometheusNode.index),
            image=self.prometheus_docker_image,
            network=docker_network,
            environment=environment,
            detach=True
        )
    
        self.containers[prometheusNode.index] = container

    def delete_instance(self, prometheusNode)->None:
        """
        Deletes a prometheus docker container
        """
        container = self.containers.get(prometheusNode.index)
        if container is not None:
            container.stop()
            container.remove()
            del self.containers[prometheusNode.index]
        

    def check_instance_health(self)->None:
        ...
