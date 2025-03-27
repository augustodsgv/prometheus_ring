docker run \
    -p 9090:9090 \
    -e PROMETHEUS_YML="$(cat prometheus.yml)" \
    augustodsgv/prometheus-ring-node \
    --storage.agent.path=/prometheus/agent \
    --config.file=/etc/prometheus/prometheus.yml \
    --agent
    # --web.console.templates=/usr/share/prometheus/consoles \
    # --web.console.libraries=/usr/share/prometheus/console_libraries \