# Prometheus ring node
This is a prometheus based image that can create a prometheus.yml from an variable,
as well as replace environmet variables found in it

for example, you can provide the following PROMETHEUS_YML in base64
```yaml
global:
  scrape_interval: 1m
rule_files:
  - "alert_rules.yml"
scrape_configs:
  - job_name: 'stress_test'
    metrics_path: /metrics
    scrape_timeout: 20s
    static_configs:
      - targets: ['{HOST}:{PORT}']
```

That, if HOST and PORT variables exists like
```
    docker run \
        -e HOST=super-host \
        -e PORT=9988 \
        prometheus-ring-node
```

the resulted prometheus.yml will be like
```yaml
global:
  scrape_interval: 1m
rule_files:
  - "alert_rules.yml"
scrape_configs:
  - job_name: 'stress_test'
    metrics_path: /metrics
    scrape_timeout: 20s
    static_configs:
      - targets: ['super-host:9988']
```

## Special variables
Some environment variables have special roles
* __PROMETHEUS_YML__: Reserved for the prometheus.yml file
* __HOSTNAME__: Pulls the hostname of the container