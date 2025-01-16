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

LOG_LEVEL = os.environ.get('LOG_LEVEL', "INFO").upper()
LOG_FILE_PATH = os.environ.get('LOG_FILE_PATH', "log.txt")

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
        },
        "file": {
            "level": "INFO",
            "formatter": "standard",
            "class": "logging.FileHandler",
            "filename": LOG_FILE_PATH,
        },
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
    node_capacity=2,
    node_min_load=0,
    node_max_load=2,
    sd_url='localhost',
    sd_port=8500,
    node_scrape_interval='10s',
    node_sd_refresh_interval='10s',
    adt=bst
    )
docker_orquestrator = DockerOrquestrator('prometheus_ring')
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

    # try:
    # except Exception as e:
    #     logger.error(f"Error fetching targets: {e}")
    #     raise HTTPException(status_code=500, detail="Internal Server Error")
