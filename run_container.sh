docker build -t prometheus-ring-api .

docker run \
    --name prometheus-ring-api \
    --network prometheus-ring \
    -p 9988:9988 \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -e API_DOCKER_NETWORK=prometheus-ring \
    -e DOCKER_PROMETHEUS_IMAGE=prometheus-ring-node \
    -e API_ENDPOINT=prometheus-ring-api \
    -e API_PORT=9988 \
    -e NODE_CAPACITY=4 \
    -e NODE_MIN_LOAD=25 \
    -e NODE_MAX_LOAD=75 \
    -e NODE_SCRAPE_INTERVAL=5s \
    -e NODE_SD_REFRESH_INTERVAL=5s \
    -e LOG_LEVEL=WARNING \
    -e METRICS_DATABASE_URL=load-balancer \
    -e METRICS_DATABASE_PORT=9009 \
    -e METRICS_DATABASE_PATH=/api/v1/push \
    prometheus-ring-api
    # -e NODE_REPLICATION_NUM=15 \
