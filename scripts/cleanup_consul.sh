#!/bin/bash

# Define Consul IP and port
CONSUL_IP="201.23.15.146"
CONSUL_PORT="8500"

# Retrieve the full list of services once
SERVICES_JSON=$(curl -s http://$CONSUL_IP:$CONSUL_PORT/v1/agent/services)

# Debug: Print the full JSON (optional)
echo "DEBUG: Full services JSON:"
echo "$SERVICES_JSON" | jq .

# Iterate over each service
for KEY in $(echo "$SERVICES_JSON" | jq -r 'keys[]'); do
    SERVICE_DETAILS=$(echo "$SERVICES_JSON" | jq -r --arg key "$KEY" '.[$key]')
    SERVICE_NAME=$(echo "$SERVICE_DETAILS" | jq -r '.Service')

    # Debug: Show each service name
    echo "DEBUG: Found service: '$SERVICE_NAME'"

    # Match if service name starts with "replica" (case-insensitive)
    if [[ "${SERVICE_NAME,,}" == replica* ]]; then
        echo "Deleting service: $SERVICE_NAME"
        RESPONSE=$(curl -s -X PUT "http://$CONSUL_IP:$CONSUL_PORT/v1/agent/service/deregister/$SERVICE_NAME")
        echo "Response: $RESPONSE"
    fi
done

echo "Cleanup completed!"
