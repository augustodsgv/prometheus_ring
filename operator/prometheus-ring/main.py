from .adt.binary_search_tree import BinarySearchTree
from .target import Target
from .service_discovery import ServiceDiscovery
from .ring import Ring, KeyNotFoundError, KeyAlreadyExistsError
from .swarm_orquestrator import SwarmOrquestrator
from .api import API
from .settings import Settings
from .log_config import LogConfig
import logging
import logging.config
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn


settings = Settings()
log_configs = LogConfig(settings.log_level)
logging.config.dictConfig(log_configs.get_logging_config())
logger = logging.getLogger(__name__)

bst = BinarySearchTree()
ring = Ring(
    node_capacity=settings.node_capacity,
    node_min_load=settings.node_min_load,
    node_max_load=settings.node_max_load,
    node_replica_count=settings.node_replication_num,
    sd_provider=settings.sd_provider,
    sd_host=settings.sd_host,
    sd_port=settings.sd_port,
    node_scrape_interval=settings.node_scrape_interval,
    node_scrape_timeout=settings.node_scrape_timeout,
    sd_refresh_interval=settings.sd_refresh_interval,
    adt=bst,
    metrics_database_url=settings.metrics_database_url,
    metrics_database_port=settings.metrics_database_port,
    metrics_database_path=settings.metrics_database_path
)


orquestrator = SwarmOrquestrator(settings.docker_prometheus_image, settings.docker_network)
service_discovery = ServiceDiscovery(settings.sd_host, settings.sd_port)
api = API(ring, orquestrator, service_discovery)

first_node = ring.node_zero             # The first node has to be created manually
orquestrator.create_node(first_node)

app = FastAPI()

@app.post("/register-target")
async def register_target(target: Target):
    try:
        api.register_target(target)
        return {"message": "Target registered successfully!"}
    except KeyAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=f"Error registering target: id {target.id} already exists")

@app.delete("/unregister-target")
async def unregister_target(target_id: str):
    try:
        api.unregister_target(target_id)
        return {"message": "Target unregistered successfully!"}
    except KeyNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Error deregistering instance: ID {target_id} not found")

@app.get("/targets")
async def get_targets():
    targets = api.build_targets_json()
    return JSONResponse(content=targets)

if __name__ == '__main__':
    uvicorn.run(app, log_config=settings.logging_config, port=9988, host='0.0.0.0')