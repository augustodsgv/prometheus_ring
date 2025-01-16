#!/bin/bash
for ((i=0; i < 100; i++)); do
    curl -X POST http://localhost:9988/register-target -H "Content-Type: application/json" -d '{
        "id": "id-id-id-'"$i"'",
        "name": "target-'"$i"'",
        "address": "172.998.'"$i"'",
        "metrics_port": 8000,
        "metrics_path": "/metrics"
    }'
done