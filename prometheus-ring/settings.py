import os

class Settings:
    docker_network = os.environ.get('DOCKER_NETWORK', "prometheus-ring")
    docker_prometheus_image = os.environ.get('DOCKER_PROMETHEUS_IMAGE', "prometheus-ring-node")

    api_endpoint = os.environ.get('API_ENDPOINT', "prometheus-ring-api")
    api_port = int(os.environ.get('API_PORT', 9988))
    node_capacity = int(os.environ.get('NODE_CAPACITY', '2'))
    node_min_load = int(os.environ.get('NODE_MIN_LOAD', '25'))
    node_max_load = int(os.environ.get('NODE_MAX_LOAD', '75'))
    node_replication_num = int(os.environ.get('NODE_REPLICATION_NUM', 1))
    node_scrape_interval = os.environ.get('NODE_SCRAPE_INTERVAL', '1m')
    sd_refresh_interval = os.environ.get('SD_REFRESH_INTERVAL', '1m')
    sd_provider = os.environ.get('SD_PROVIDER', 'consul')
    sd_port = os.environ.get('SD_PORT', 8500)
    sd_host = os.environ.get('SD_HOST', 'consul')
    metrics_database_url = os.environ.get('METRICS_DATABASE_URL', None)
    metrics_database_port = os.environ.get('METRICS_DATABASE_PORT', None)
    metrics_database_path = os.environ.get('METRICS_DATABASE_PATH', None)
    log_level = os.environ.get('LOG_LEVEL', "INFO").upper()

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
        },
        "handlers": {
            "default": {
                "level": log_level,
                "formatter": "standard",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            }
        },
        "loggers": {
            "": {
                "level": log_level,
                "handlers": ["default"],
                "propagate": False,
            },
            "uvicorn.error": {
                "level": log_level,
                "handlers": ["default"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": log_level,
                "handlers": ["default"],
                "propagate": False,
            },
        },
    }
