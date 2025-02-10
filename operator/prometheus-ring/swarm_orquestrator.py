from .node import Node
import docker
from docker.models.services import Service
import logging
import time
logger = logging.getLogger(__name__)

API_MAX_RETRIES = 5

class UpdatingServiceError(Exception):
    ...

class SwarmOrquestrator:
    """
    Docker swarm interface to manage prometheus nodes
    """
    def __init__(
            self,
            prometheus_docker_image: str = 'prom/prometheus',
            docker_network: str = 'prometheus-ring',
            docker_url: str = 'unix://var/run/docker.sock',
        )->None:

        self.client = docker.DockerClient(base_url=docker_url)
        self.docker_network = docker_network
        self.prometheus_docker_image = prometheus_docker_image
        self.docker_url = docker_url
        self.services :dict[str, Service]= dict()        # Keeps track of each node's service

    def create_node(
            self,
            node: Node,
            environment: dict | None = None,
        )->None:
        """
        Instanciates a docker swarm service for a prometheus node
        """
        if environment is None:
            environment = dict()

        environment['PROMETHEUS_YML'] = node.yaml

        endpoint_spec = docker.types.EndpointSpec(ports={node.port: 9090})              # Configuring ports
        service_envs: list[str] = [f'{env}={val}' for env, val in environment.items()]
        service: Service = self.client.services.create(
            image=self.prometheus_docker_image,
            env=service_envs,
            name=f'prometheus-{node.index}',
            endpoint_spec=endpoint_spec,
            networks=[self.docker_network]
            # stop_grace_period= '1m',                                                    # Grace period for stopping the service
        )
        self.services[node.index] = service
        """
        Seems like each change made by service kwargs create a new version of it,
        throwing ("rpc error: code = Unknown desc = update out of sequence").
        Also, there may be a racing condition between the service update and
        the function run. Thus, we are gonna making multiple tries
        """
        for attemp in range(API_MAX_RETRIES):
            try:
                updated_service: Service = self.client.services.get(service.id)
                updated_service.scale(node.replica_count)
                break
            except docker.errors.APIError as e:
                if "update out of sequence" in str(e):
                    logger.warning(f'Attemp {attemp} of attaching port {node.port} to service {service.name} failed: {str(e)}. Retring...')
                    time.sleep(2 ** attemp)                                                                             # Progressively increses the await time for the next
        else:
            logger.error(f'Failed attaching port {node.port} to {service.name} after {API_MAX_RETRIES} attemps.')
            raise UpdatingServiceError(f'Failed attaching port {node.port} to {service.name} after {API_MAX_RETRIES} attemps.')

        for attemp in range(API_MAX_RETRIES):
            try:
                updated_service: Service = self.client.services.get(service.id)
                updated_service.scale(node.replica_count)
                break
            except docker.errors.APIError as e:
                if "update out of sequence" in str(e):
                    logger.warning(f'Attemp {attemp} of scaling up service {service.name} failed: {str(e)}. Retring...')
                    time.sleep(2 ** attemp)                                                                             # Progressively increses the await time for the next
        else:
            logger.error(f'Failed scaling up service {service.name} after {API_MAX_RETRIES} attemps.')
            raise UpdatingServiceError(f'Failed scaling up service {service.name} after {API_MAX_RETRIES} attemps.')


    def delete_node(self, node: Node)->None:
        """
        Deletes a prometheus docker container
        """
        print(f'Deleting node {node} from swarm')
        logger.debug(f'Deleting node {node} from swarm')
        node_service = self.services.get(node.index)
        result = node_service.remove()
        print(f'Result: {result}')
        logger.debug(f'Result: {result}')


    def check_health_node(self, node: Node)->None:
        """
        Heath checks if a prometheus node is running.
        For now, i can only check if service is running on current cluster 
        prometheus health check endpoint
        """
        # TODO: implement heatlh check

if __name__ == '__main__':
    node1 = Node(0, 100, 'consul', 9090, 'consul', '8500', '1m', '1m', 3)
    node2 = Node(1, 100, 'consul', 9091, 'consul', '8501', '1m', '1m', 3)
    node3 = Node(2, 100, 'consul', 9092, 'consul', '8502', '1m', '1m', 3)
    orquestrator = SwarmOrquestrator('prometheus-ring-node')
    orquestrator.create_node(node1)
    orquestrator.create_node(node2)
    orquestrator.create_node(node3)
    input()
    orquestrator.delete_node(node1)
    orquestrator.delete_node(node2)
    orquestrator.delete_node(node3)
