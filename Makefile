# Version and name variables
RELEASE := 0.1-alpha
NAMESPACE := augustodsgv
STACK_NAME := prometheus-ring

IMAGES := operator node mimir
IMAGE_OPERATOR := $(NAMESPACE)/prometheus-ring
IMAGE_NODE := $(NAMESPACE)/prometheus-ring-node
IMAGE_MIMIR := $(NAMESPACE)/custom-mimir

.PHONY: help build build-operator build-node build-mimir deploy destroy

help:
	@echo "Makefile to manage the Prometheus Ring project"
	@echo "Available commands:"
	@echo "  build         - Build and push all Docker images"
	@echo "  build-operator - Build and push the operator image"
	@echo "  build-node     - Build and push the node image"
	@echo "  build-mimir    - Build and push the Mimir image"
	@echo "  deploy        - Deploy the Docker stack"
	@echo "  destroy       - Remove the services and the Docker stack"

build: docker-login $(patsubst %, build-%, $(IMAGES))

docker-login:
	@echo "Logging in to Docker..."
	@docker login || { echo "Login failed"; exit 1; }

build-operator:
	@echo "Building and pushing the operator image..."
	docker build -t $(IMAGE_OPERATOR):$(RELEASE) operator
	docker push $(IMAGE_OPERATOR):$(RELEASE)

build-node:
	@echo "Building and pushing the node image..."
	docker build -t $(IMAGE_NODE):$(RELEASE) prometheus-ring-node
	docker push $(IMAGE_NODE):$(RELEASE)

deploy:
	@echo "Deploying the stack..."
	docker stack deploy --compose-file compose.yaml $(STACK_NAME)

destroy:
	@echo "Removing node services..."
	docker service ls --format '{{.ID}} {{.Image}}' | grep "$(IMAGE_NODE)" | awk '{print $$1}' | xargs -r docker service rm
	@echo "Removing the stack..."
	docker stack rm $(STACK_NAME)
