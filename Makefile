help:
	@echo "make [build|deploy|destroy]"

build:
	docker login
	make build-operator
	make build-node
	make build-mimir

build-operator:
	docker build -t augustodsgv/prometheus-ring operator
	docker push augustodsgv/prometheus-ring

build-node:
	docker build -t augustodsgv/prometheus-ring-node prometheus-ring-node
	docker push augustodsgv/prometheus-ring-node

build-mimir:
	docker build -t augustodsgv/custom-mimir custom-mimir
	docker push augustodsgv/custom-mimir

deploy:
	@export MIMIR_YAML="$(shell cat ./mimir/mimir.yaml)"; \
	envsubst < compose.yaml | docker stack deploy -c - prometheus-ring

destroy:
	docker service  ls --format json | jq -r '. | select(.Image == "augustodsgv/prometheus-ring-node") | .ID' | xargs -I {} docker service rm {}
	docker stack rm prometheus-ring
