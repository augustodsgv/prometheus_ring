docker run \
    --name custom \
    -p 8080:8080 \
    -e MIMIR_YAML="$(cat mimir.yaml)" \
    mimir-teste