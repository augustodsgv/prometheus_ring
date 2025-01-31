prometheus_yml_base64=$(base64 -w 0 prometheus.yml)
echo $prometheus_yml_base64
docker volume create prometheus-node-test
docker run -v prometheus-node-test:/agent  -p 9090:9090 -e PROMETHEUS_YML=$prometheus_yml_base64 prometheus-ring-node