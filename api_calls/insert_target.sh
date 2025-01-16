#!/bin/bash

curl -X POST http://localhost:9988/register-target -H "Content-Type: application/json" -d '{
    "id": "id-id-id-678",
    "name": "target-678",
    "address": "172.998.678",
    "metrics_port": 8000,
    "metrics_path": "/metrics"
}'