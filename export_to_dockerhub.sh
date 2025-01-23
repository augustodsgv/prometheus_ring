if [ -z "$1" ]; then
    read -p "Enter your DockerHub username: " DOCKERHUB_USERNAME
else
    DOCKERHUB_USERNAME=$1
fi
docker login
docker build . -t $(echo $DOCKERHUB_USERNAME)/prometheus_ring
echo $DOCKERHUB_USERNAME
docker push $(echo $DOCKERHUB_USERNAME)/prometheus_ring