docker run \
    --name custom-mimir \
    -p 8080:8080 \
    -v ./mimir.yaml:/etc/mimir.yaml \
    -v ./alertmanager.yaml:/etc/alertmanager-fallback-config.yaml \
    augustodsgv/custom-mimir