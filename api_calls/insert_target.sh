#!/bin/bash

curl -X POST http://localhost:9988/register-target -H "Content-Type: application/json" -d '{
    "id": "4",
    "name": "replica 4",
    "address": "mimir-cloud_metrics_generator-4",
    "metrics_port": 8000,
    "metrics_path": "/metrics"
}'