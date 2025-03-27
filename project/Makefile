.PHONY: help build build-operator build-node

help:
	@echo "Usage: make [build]"
	@echo "  build         - Build all Docker images"

build: build-operator build-node

build-operator:
	docker build -t augustodsgv/prometheus-ring operator
	docker push augustodsgv/prometheus-ring

build-node:
	docker build -t augustodsgv/prometheus-ring-node prometheus-ring-node
	docker push augustodsgv/prometheus-ring-node