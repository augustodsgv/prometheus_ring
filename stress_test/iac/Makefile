TF_DIR ?= ./terraform
TF_AUTH_FILE ?= $(TF_DIR)/auth.sh
KUBECONFIG ?= ./k8s/kubeconfig.yaml
HELM_DIR ?= ./k8s
INVENTORY_FILE ?= ./ansible/inventory.yaml
ANSIBLE_PLAYBOOK ?= ./ansible/playbook.yaml

.PHONY: help deploy destroy terraform inventory ansible clean all

help:
	@echo "Usage: make [deploy|destroy|terraform|inventory|ansible|clean|all]"
	@echo "  deploy        - Deploy prometheus ring on docker swarm and mimir on k8s"
	@echo "  destroy       - Remove running services"
	@echo "  terraform     - Run Terraform initialization and apply"
	@echo "  inventory     - Generate Ansible inventory from Terraform output"
	@echo "  ansible       - Runs the Ansible playbook"

# Infraestructure setup
terraform:
	@echo Building terraform infraestructure...
	terraform -chdir=$(TF_DIR) apply

inventory:
	@echo Building ansible inventory...
	terraform -chdir=$(TF_DIR) output -json | ./build-inventory $(INVENTORY_FILE)

terraform-destroy:
	terraform -chdir=$(TF_DIR) destroy

ansible:
	@echo "Running Ansible Playbook..."
	ansible-playbook -i $(INVENTORY_FILE) $(ANSIBLE_PLAYBOOK)

## Deploy Prometheus Ring on docker swarm machines
deploy:
	@echo "Deploy Prometheus Ring on Docker Swarm..."
	@MANAGER_NODE=$$(terraform -chdir=$(TF_DIR) output -json | jq -r '.prom_stress_test_managers_ips.value["manager-0"].public_ip') && \
	scp -o StrictHostKeyChecking=no compose.yaml ubuntu@$$MANAGER_NODE:/tmp/ && \
	ssh -o StrictHostKeyChecking=no ubuntu@$$MANAGER_NODE "docker stack deploy -c /tmp/compose.yaml prom_stress_test"

destroy:
	@echo "Destroying Prometheus Ring deployment..."
	@MANAGER_NODE=$$(terraform -chdir=$(TF_DIR) output -json | jq -r '.prom_stress_test_managers_ips.value["manager-0"].public_ip') && \
	ssh -o StrictHostKeyChecking=no ubuntu@$$MANAGER_NODE docker stack rm prom_stress_test
