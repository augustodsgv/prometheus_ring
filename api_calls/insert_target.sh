#!/bin/bash

curl -X POST http://localhost:9988/register-target -H "Content-Type: application/json" -d '{
    "id": "54172367-133e-4cd5-9f73-8598b7c85435",
    "name": "vmzona",
    "address": "54172367-133e-4cd5-9f73-8598b7c85435",
    "metrics_port": 8000,
    "metrics_path": "/metrics"
}'