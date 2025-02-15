#!/bin/bash

# Parse the JSON data (replace with your actual JSON file or pipe)
json_data=$1

# Function to extract IP addresses and generate Ansible inventory
generate_inventory() {
  local group_name="$1"
  local data="$2"

  echo "    ${group_name}:"
  echo "      hosts:"

  # Iterate over each host in the group
  jq -r ".value | keys[]" <<< "$data" | while read -r host_name; do
    private_ip=$(jq -r ".value.\"$host_name\".private_ip" <<< "$data")
    public_ip=$(jq -r ".value.\"$host_name\".public_ip" <<< "$data")

    # Construct the host entry
    echo "        ${host_name}:"
    echo "          ansible_host: ${public_ip}"
    echo "          private_ip: ${private_ip}"
  done
}


echo "all:"
echo "  vars:"
echo "    ansible_user: ubuntu"
echo "    ansible_ssh_private_key_file: /home/augusto/.ssh/ed25519"
echo "    ansible_ssh_common_args: '-o StrictHostKeyChecking=no'"
echo "  children:"

# Generate inventory for managers
managers_data=$(jq -r '.prometheus_ring_managers_ips' <<< "$json_data")
generate_inventory "managers" "$managers_data"

# Generate inventory for workers
workers_data=$(jq -r '.prometheus_ring_workers_ips' <<< "$json_data")
generate_inventory "workers" "$workers_data"