from src.ring.prometheus_node import PrometheusNode
from src.orquestrator.docker_orquestrator import DockerOrquestrator
from src.ring.prometheus_ring import PrometheusRing
from src.adt.binary_search_tree import BinarySearchTree
from src.service_discovery.prometheus_ring_sd import PrometheusRingSD
from src.ring.target import Target
import logging

logging.basicConfig(level=logging.DEBUG, filename='logs')
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    adt = BinarySearchTree()
    ring = PrometheusRing(
        node_capacity=2,
        node_min_load=0,
        node_max_load=1,
        sd_url='localhost',
        sd_port=8500,
        node_scrape_interval='1m',
        node_sd_refresh_interval='1m',
        adt=adt
        )
    
    orquestrator = DockerOrquestrator('prometheus_ring')
    sd = PrometheusRingSD(ring)
    t1 = Target(id='abcd', name='abcd', address='abdc')
    t2 = Target(id='efgh', name='efgh', address='abdc')
    t3 = Target(id='ijkl', name='ijkl', address='abdc')
    t4 = Target(id='mnop', name='mnop', address='abdc')
    t5 = Target(id='qrst', name='qrst', address='abdc')
    t6 = Target(id='uvwx', name='uvwx', address='abdc')

    sd.register_target(t1)
    sd.register_target(t2)
    sd.register_target(t3)
    sd.register_target(t4)
    sd.register_target(t5)
    sd.register_target(t6)
    for node in ring.get_nodes():
        logger.info(node)
        sd.register_target(t1)
    sd.deregister_target(t2)
    sd.deregister_target(t3)
    sd.deregister_target(t4)
    sd.deregister_target(t5)
    sd.deregister_target(t6)
