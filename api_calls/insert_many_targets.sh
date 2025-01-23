#!/bin/bash
for ((i=0; i < 15; i++)); do
    curl -X POST http://localhost:9988/register-target -H "Content-Type: application/json" -d '{
    "id": "'$i'",
    "name": "replica '$i'",
    "address": "mimir-cloud_metrics_generator-'$i'",
    "metrics_port": 8000,
    "metrics_path": "/metrics"
}'
done