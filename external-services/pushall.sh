#!/bin/bash

# Docker Hub 사용자 이름
DOCKER_USERNAME="kasd0134"

# 서비스 목록
IMAGES=("userservice" "parkservice" "facilityservice" "ticketservice")
DIRECTORIES=("user_service" "park_service" "facility_service" "ticket_service")

# 현재 날짜를 태그로 사용
TAG="latest"

# 각 서비스에 대해 반복
for i in "${!IMAGES[@]}"
do
    IMAGE=${IMAGES[$i]}
    DIRECTORY=${DIRECTORIES[$i]}
    
    docker buildx build --platform linux/amd64,linux/arm64 -t kasd0134/msa-$IMAGE:latest $DIRECTORY --push
    
    echo "$IMAGE has been built and pushed successfully."
    echo "-------------------------------------------"
done

echo "All services have been built and pushed to Docker Hub."