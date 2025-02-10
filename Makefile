help:
	@echo "make [build|deploy|destroy]"

build:
	build-ring
	build-node
	build-mimir

build-ring:
	docker login
	docker build -t augustodsgv/prometheus-ring .
	docker push augustodsgv/prometheus-ring

build-node:
	docker login
	docker build -t augustodsgv/prometheus-ring-node prometheus-ring-node
	docker push augustodsgv/prometheus-ring-node

build-mimir:
	docker login
	docker build -t augustodsgv/custom-mimir custom-mimir
	docker push augustodsgv/custom-mimir

deploy:
	docker stack deploy --compose-file compose.yaml prometheus-ring

destroy:
	docker service ls  | grep prometheus-ring-node | awk '{print $1}' | while read -r service; do docker service rm "$$service"; done
	docker stack rm prometheus-ring
