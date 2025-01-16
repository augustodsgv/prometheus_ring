from src.ring.prometheus_node import PrometheusNode
from src.orquestrator.docker_orquestrator import DockerOrquestrator
from src.ring.prometheus_ring import PrometheusRing
from src.adt.binary_search_tree import BinarySearchTree
from src.ring.target import Target
from src.api import API
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from src.ring.errors.ring_errors import *
from src.ring.errors.node_errors import *
import os

API_DOCKER_NETWORK = os.environ.get('API_DOCKER_NETWORK', "ring-api-network")
DOCKER_PROMETHEUS_IMAGE = os.environ.get('DOCKER_PROMETHEUS_IMAGE', "prometheus-ring-node")

API_ENDPOINT = os.environ.get('API_ENDPOINT', "prometheus-ring-api")
API_PORT = int(os.environ.get('API_PORT', 9988)
)
NODE_CAPACITY=int(os.environ.get('NODE_CAPACITY', '2'))
NODE_MIN_LOAD=int(os.environ.get('NODE_MIN_LOAD', '2'))
NODE_MAX_LOAD=int(os.environ.get('NODE_MAX_LOAD', '3'))
NODE_SCRAPE_INTERVAL=os.environ.get('NODE_SCRAPE_INTERVAL', '1m')
NODE_SD_REFRESH_INTERVAL=os.environ.get('NODE_SD_REFRESH_INTERVAL', '1m')

# SD_URL = os.environ.get('SD_URL', "prometheus-ring-api")
# SD_PORT = os.environ.get('SD_PORT', "prometheus-ring-api")        # In our case, the api IS the service discovery

LOG_LEVEL = os.environ.get('LOG_LEVEL', "INFO").upper()
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
    },
    "handlers": {
        "default": {
            "level": "INFO",
            "formatter": "standard",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",  # Default is stderr
        }
    },
    "loggers": {
        "": {  # root logger
            "level": LOG_LEVEL,
            "handlers": ["default"],
            "propagate": False,
        },
        "uvicorn.error": {
            "level": "DEBUG",
            "handlers": ["default"],
        },
        "uvicorn.access": {
            "level": "DEBUG",
            "handlers": ["default"],
        },
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

bst = BinarySearchTree()
ring = PrometheusRing(
    node_capacity=NODE_CAPACITY,
    node_min_load=NODE_MIN_LOAD,
    node_max_load=NODE_MAX_LOAD,
    sd_url=API_ENDPOINT,
    sd_port=API_PORT,
    node_scrape_interval=NODE_SCRAPE_INTERVAL,
    node_sd_refresh_interval=NODE_SD_REFRESH_INTERVAL,
    adt=bst
    )

docker_orquestrator = DockerOrquestrator(DOCKER_PROMETHEUS_IMAGE, API_DOCKER_NETWORK)
api = API(ring, docker_orquestrator)
# The first node has to be created manually
first_node = ring.get_initial_node()
docker_orquestrator.create_instance(first_node)

app = FastAPI()

@app.post("/register-target")
def register_target(target: Target):
    try:
        api.register_target(target)
        return {"message": "Target registered successfully!"}
    except KeyAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=f"Error registering target: id {target.id} already exists")

@app.delete("/unregister-target")
def unregister_target(target_id: str):
    try:
        api.unregister_target(target_id)
        return {"message": "Target unregistered successfully!"}
    except KeyNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Error deregistering instance: ID {target_id} not found")

@app.get("/targets")
def get_targets():
    targets = api.build_targets_json()
    logger.debug(f'targets {targets}')
    return JSONResponse(content=targets)
