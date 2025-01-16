# Prometheus ring
Prometheus ring is an application intended for orchestrating prometheus instances
in a consistent hash table.
The idea is that the prometheus ring is able to receive applications to monitor and
scales up the sistem on demand

## The ring
The ring itself is a consistent hash table that stores the items by it's hash.
It stores both the applications and the nodes that monitor then.

## The API
The API is the interface by where the clients can register their applications to be montiored
It could be a nice thing that this would also provide the visualization of the metrics

## The Service Discovery
To make the prometheus nodes work as a real cluster, a service discovery is needed
to tell prometheus instance what applications it should lookup to colect the metrics

## The orchestrator
To launch, delete and maintain the prometheus instances, the orchestrator comes in hand.
It's will be able to use a infrastructure like docker (or kubernetes? who knows) to 
Launch the instances

## Running the project
The docker container provides an help while launching this application, but some configuration is still needed.

### Environmento variables
* __API_DOCKER_NETWORK__: The name of the Docker network used for API communication. Defaults to "ring-api-network"

* __DOCKER_PROMETHEUS_IMAGE__: The Docker image used for Prometheus launching prometheus nodes. Defaults to "prometheus-ring-node".

* __API_ENDPOINT__: The endpoint for the API. Defaults to "prometheus-ring-api" 

* __API_PORT__: The port number for the API. Defaults to 9988

* __NODE_CAPACITY__: The maximum capacity of the node. Defaults to '2'.

* __NODE_MIN_LOAD__: The minimum load of the node before it's killed. Defaults to '2'.

* __NODE_MAX_LOAD__: The maximum load of the node before it splits Defaults to '3'.

* __NODE_SCRAPE_INTERVAL__: The interval at which the node scrapes it's data. Defaults to '1m'

* __NODE_SD_REFRESH_INTERVAL__: The interval at which the nodes fetches discovery for discovering new targets is refreshed. Defaults to '1m'.

* __LOG_LEVEL__: The logging level for the application. Defaults to "INFO".