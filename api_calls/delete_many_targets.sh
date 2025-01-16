#!/bin/bash
for ((i=0; i < 100; i++)); do
    curl -X DELETE "http://localhost:9988/unregister-target/target_id?id=id-id-id-$i"
    sleep 1
done