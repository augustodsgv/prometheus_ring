#!/bin/bash
EXPORTER_ADDRS=("172.30.0.20" "172.30.0.125" "172.30.0.79" "172.30.0.78" "172.30.0.105" "172.30.0.89" "172.30.0.55" "172.30.0.3" "172.30.0.100" "172.30.0.116")

EXPORTER_BASE_PORT=8000
API_ADDR="201.23.2.4"
API_PORT="9988"

register_target(){
    id=$1
    addr=$2
    port=$3

    curl_cmd=$(cat << EOF
curl -X POST http://$API_ADDR:$API_PORT/register-target -H "Content-Type: application/json" -d '{
    "id": "'$id'",
    "name": "replica '$id'",
    "address": "'$addr'",
    "metrics_port": "'$port'",
    "metrics_path": "/metrics"
}'
EOF
)
    echo "$curl_cmd"  # Print the command
    eval "$curl_cmd" # Uncomment to actually execute the command
}

set_test_targets(){
    first_target=$1
    last_target=$2
    for ((i=first_target; i<last_target; i++)); do
        addr_index=$((($i - 1) % ${#EXPORTER_ADDRS[@]}))
        addr="${EXPORTER_ADDRS[$addr_index]}" # Get the address from the array
        port=$((EXPORTER_BASE_PORT + i)) # Calculate the port
        # register_target "$i" "$addr" "$port"
        register_target "$(uuidgen)" "$addr" "$port"
    done
}

replica_counts=(3000 4000 5000 6000 7000 8000)
last_test=0
for replica_count in "${replica_counts[@]}"; do
  echo "Running test with $replica_count replicas"
  set_test_targets $last_test $replica_count
  echo "Press any key to jump to next load..."
  read
  # sleep 1800
  last_test=$replica_count
done