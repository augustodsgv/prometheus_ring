from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    docker_network: str = "prometheus-ring"
    docker_prometheus_image: str = "prometheus-ring-node"

    api_endpoint: str = "prometheus-ring-api"
    api_port: int = 9988
    node_capacity: int = 2
    node_min_load: int = 25
    node_max_load: int = 75
    node_replication_num: int = 1
    node_scrape_interval: str = '1m'
    node_scrape_timeout: str = '20s'
    sd_refresh_interval: str = '1m'
    sd_provider: str = 'consul'
    sd_port: int = 8500
    sd_host: str = 'consul'
    metrics_database_url: str = ""
    metrics_database_port: int = 8000
    metrics_database_path: str = ""
    log_level: str = "INFO"

if __name__ == '__main__':
    settings = Settings()
    print(settings.model_dump())
