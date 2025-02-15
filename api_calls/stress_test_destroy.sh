#!/bin/bash
EXPORTER_ADDRS=("172.30.0.20" "172.30.0.125" "172.30.0.79" "172.30.0.78" "172.30.0.105" "172.30.0.89" "172.30.0.55" "172.30.0.3" "172.30.0.100" "172.30.0.116")

API_ADDR="201.23.2.4"
API_PORT="9988"

delete_test_targets(){
    first_target=$1
    last_target=$2
    for ((i=first_target; i<last_target; i++)); do
        curl -X DELETE "http://$API_ADDR:9988/unregister-target?target_id=$i"
    done
}

replica_counts=(3 500 1000 1500 2000 3000 6000 8000)
last_test=0

for replica_count in "${replica_counts[@]}"; do
  echo "Running test with $replica_count replicas"
  delete_test_targets $last_test $replica_count
  echo "Press any key to jump to next load..."
  read
  # sleep 1800
  last_test=$replica_count
done